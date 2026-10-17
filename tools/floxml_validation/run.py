"""Run with uv run --locked python -m tools.floxml_validation.run."""

import argparse
import json
import platform
import subprocess
from collections import Counter
from pathlib import Path

from lxml import etree

from packstudio.exporters.floxml import export_floxml
from packstudio.templates.package_library.catalog import definition, generate
from packstudio.templates.package_library.core.materials import production_materials
from packstudio.templates.package_library.core.parameters import TemplateRequest
from packstudio.templates.package_library.core.preset_request import resolve_preset_request
from tools.floxml_validation.cases import ROOT, archived_cases, fresh_cases
from tools.floxml_validation.classification import classify
from tools.floxml_validation.compare import compare
from tools.floxml_validation.native import fingerprint
from tools.floxml_validation.native_suite import suite
from tools.floxml_validation.reader import Box, read


def raw_model(request):
    item = definition(request.template_id)
    resolved, _ = resolve_preset_request(item, request)
    values = item.validate_request(resolved)
    built = item.builder(values, item.resolve_material_request(resolved, values))
    materials = {
        **production_materials(),
        **{m.id: m for m in built.materials},
        **{m.id: m for m in request.custom_materials},
    }
    boxes = []
    for block in [*built.drafts, *built.blocks]:
        origin = block.origin
        size = block.size
        if hasattr(origin, "x"):
            origin = tuple(getattr(origin, a) for a in "xyz")
            size = tuple(getattr(size, a) for a in "xyz")
        boxes.append(
            Box(
                block.name,
                origin,
                size,
                block.material_id,
                role=block.structure_type.value,
                priority=getattr(block, "priority", 20),
                identity=block.id,
            )
        )
    return boxes, {
        key: (*[getattr(m.conductivity, a) for a in "xyz"], m.density, m.specific_heat)
        for key, m in materials.items()
    }


def execute_case(case, directory, schema):
    request = case["request"]
    output = directory / case["id"]
    output.mkdir(parents=True, exist_ok=True)
    payload = request.model_dump(mode="json")
    (output / "request.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    result = {key: case[key] for key in ("id", "template", "kind")}
    result.update(
        {
            "request": payload,
            "native_path": str(case["native"]),
            "native_sha256": fingerprint(case["native"]),
            "input_source": str(case["source"]),
            "input_source_sha256": fingerprint(case["source"]),
            "native_software": "FloTHERM PACK 2504; archive capture or fresh replay",
            "detail_path": str(output / "comparison.json"),
        }
    )
    result.update(
        {key: case[key] for key in ("native_des_sha256", "native_material_sha256") if key in case}
    )
    try:
        drafts, materials = raw_model(request)
        model = generate(request)
        floxml = export_floxml(model)
        schema.assertValid(etree.fromstring(floxml))
        exported_path = output / "packstudio.floxml"
        exported_path.write_bytes(floxml)
        result["export_sha256"] = fingerprint(exported_path)
        native, exported = read(case["native"]), read(exported_path)
        # Full field-level exporter round trip, independent of native parity.
        by_id = {box.name: box for box in exported.boxes}
        for block in model.blocks:
            box = by_id[block.id]
            assert box.material == block.material_id
            assert all(
                abs(getattr(block.origin, a) - box.origin[i]) < 1e-10 for i, a in enumerate("xyz")
            )
            assert all(
                abs(getattr(block.size, a) - box.size[i]) < 1e-10 for i, a in enumerate("xyz")
            )
        assert len(by_id) == len(model.blocks)
        for material in model.materials:
            assert exported.materials[material.id] == (
                material.conductivity.x,
                material.conductivity.y,
                material.conductivity.z,
                material.density,
                material.specific_heat,
            )
        assert (
            abs(
                sum(s["power_w"] for s in exported.sources)
                - sum(s.power_w for s in model.heat_sources)
            )
            < 1e-10
        )
        details = compare(native, exported, drafts, materials)
        details["findings"] = classify(case, details)
        result["findings"] = details["findings"]
        (output / "comparison.json").write_text(
            json.dumps(details, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        result["status"] = "compared"
        result["raw"] = {key: value for key, value in details["raw"].items() if key != "matches"}
        result["raw"]["matched_count"] = len(details["raw"]["matches"])
        result["normalized"] = {
            key: value for key, value in details["normalized"].items() if key != "differences"
        }
        result["difference_count"] = len(details["normalized"]["differences"])
        result["difference_examples"] = details["normalized"]["differences"][:5]
        result["power"] = {
            key: value
            for key, value in details["sources"].items()
            if key
            in {
                "pack_power_w",
                "packstudio_power_w",
                "total_power_equal",
                "total_power_difference_w",
            }
        }
    except ValueError as error:
        result.update(status="generation_or_reader_rejected", error=str(error))
        result["findings"] = [
            {
                "category": "confirmed_implementation_defect"
                if case["id"] == "qfp-negative"
                else "insufficient_evidence",
                "id": "F3-negative-wire-height"
                if case["id"] == "qfp-negative"
                else "U3-rejected-request-or-reader",
                "evidence": str(error),
                "status": "open",
            }
        ]
    (output / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "tmp/floxml/comparison")
    parser.add_argument("--native-dir", type=Path)
    parser.add_argument("--installation", type=Path)
    parser.add_argument("--baselines-only", action="store_true")
    parser.add_argument("--native-only", action="store_true")
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--case", action="append", dest="case_ids")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.evidence_dir:
        manifest = json.loads((args.evidence_dir / "manifest.json").read_text(encoding="utf-8"))
        cases = [
            {
                **item,
                "request": TemplateRequest.model_validate(item["request"]),
                "native": args.evidence_dir / item["native"],
                "source": args.evidence_dir / item["source"],
            }
            for item in manifest["cases"]
        ]
    else:
        cases = list(archived_cases())
    if args.baselines_only:
        cases = [c for c in cases if c["kind"] == "baseline"]
    if args.native_only:
        cases = []
    native_run = None
    if args.native_dir:
        native_cases = fresh_cases(args.native_dir.resolve())
        native_run = suite(args.installation, native_cases, args.native_dir.resolve())
        cases.extend(native_cases)
    if args.case_ids:
        cases = [c for c in cases if c["id"] in args.case_ids]
        if {c["id"] for c in cases} != set(args.case_ids):
            raise ValueError("unknown requested case IDs")
    schema = etree.XMLSchema(etree.parse(str(ROOT / "output_format/floxml/xmlSchema.xsd")))
    results = []
    for index, case in enumerate(cases):
        if args.evidence_dir and (
            fingerprint(case["native"]) != case["native_sha256"]
            or fingerprint(case["source"]) != case["input_source_sha256"]
        ):
            raise ValueError(f"evidence fingerprint mismatch: {case['id']}")
        results.append(execute_case(case, args.output, schema))
        if index % 10 == 0:
            print(f"{index + 1}/{len(cases)} {case['id']}", flush=True)
    summary = {
        "schema": "packstudio.floxml-comparison/v1",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "python": platform.python_version(),
        "native_run": native_run,
        "tolerances": {
            "geometry_abs_mm": 1e-7,
            "property_rel": 1e-7,
            "property_abs": 1e-8,
            "intersection_volume_mm3": 1e-12,
            "clip_axis_mm": 1e-10,
            "power_abs_w": 1e-10,
        },
        "counts": dict(Counter(r["status"] for r in results)),
        "cases": results,
    }
    path = args.output / "results.json"
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(summary["counts"], path, flush=True)


if __name__ == "__main__":
    main()
