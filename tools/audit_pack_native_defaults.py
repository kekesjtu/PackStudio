"""Cross-check native snapshots against DES records, known rules and archived FloXML."""

import json
import math
from collections import Counter
from pathlib import Path

from lxml import etree

from packstudio.templates.package_library.catalog import definitions
from packstudio.templates.package_library.core.parameters import TemplateRequest

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "flotherm_pack_data/installation"


def properties(record: dict) -> dict[str, str | None]:
    """Expose only unambiguous fields; repeated group-specific materials are omitted."""
    values = {}
    ambiguous = set()
    for group in record["groups"]:
        for prop in group["properties"]:
            name, value = prop["name"], prop["value"]
            if name in values and values[name] != value:
                ambiguous.add(name)
            values[name] = value
    return {name: value for name, value in values.items() if name not in ambiguous}


def source_audit(records: list[dict]) -> dict:
    sources = {}
    for path in (ROOT / "default_parameters/flotherm").glob("*.json"):
        for record in json.loads(path.read_text(encoding="utf-8"))["records"]:
            sources[(path.stem, record["id"])] = record
    checked = 0
    for record in records:
        source = sources[(record["family"], record["preset"])]
        assert source["source_sha256"] == record["source_sha256"]
        values = properties(record)
        for raw_name, native_name in (
            ("Ld", "dieLengthLd"),
            ("Wd", "dieWidthWd"),
            ("td", "dieThicknessTd"),
        ):
            assert math.isclose(
                float(source["raw_fields"][raw_name]), float(values[native_name]), abs_tol=1e-12
            ), (record["preset"], native_name)
            checked += 1
    return {"source_hashes_checked": len(records), "die_dimensions_checked": checked}


def rule_audit(records: list[dict], four_layer: list[dict]) -> dict:
    checked = 0
    for record in records + four_layer:
        values = properties(record)
        four = record["wizard"] == "4-Layer"
        if record["family"] == "pbga_wb":
            small = (
                float(values["substrateLengthD"]) <= 23 and float(values["substrateWidthE"]) <= 30
            )
            expected = 0.36 if small and not four else 0.56
            assert float(values["substrateThicknessA2"]) == expected
            for name in ("numberOfThermalViasInXNVx", "numberOfThermalViasInYNVy"):
                assert int(values[name]) == (3 if four else 5)
            assert values["viaPitchEv"] == values["ballPitchE"]
            checked += 4
        elif record["family"] == "chip_array":
            assert float(values["substrateThicknessA2"]) == (0.56 if four else 0.36)
            checked += 1
        if record["family"] in {"pbga_wb", "chip_array"}:
            rows = next(g["metal_layer_rows"] for g in record["groups"] if g["metal_layer_rows"])
            assert sum(row["thickness_m"] is not None for row in rows) == (4 if four else 2)
            checked += 1
    return {"conditional_rule_assertions": checked}


def xml_audit(records: list[dict], four_layer: list[dict]) -> list[dict]:
    cases = [
        ("fbga_fsbga", "baseline", "dielectric", records),
        ("flip_chip_cbga", "baseline", "substrate", records),
        ("flip_chip_pbga", "baseline", "core_dielectric", records),
        ("wirebond_pbga", "baseline", "dielectric", records),
        (
            "fbga_fsbga",
            "xml_variations/option_switches/opt_v2_c003_substratelayer_4_layer",
            "dielectric",
            four_layer,
        ),
        (
            "wirebond_pbga",
            "xml_variations/option_switches/opt_v2_c003_substratelayer_4_layer",
            "dielectric",
            four_layer,
        ),
    ]
    results = []
    for template, folder, cuboid, snapshots in cases:
        directory = ROOT / "flotherm_pack_data/templates" / template / folder
        script = etree.parse(str(directory / "script.xml"))
        preset = script.xpath("//new_value[@property_name='jedecFootprint']/@new_value")[0]
        record = next(item for item in snapshots if item["preset"] == preset)
        model = etree.parse(str(directory / "model.xml"))
        thickness = float(model.xpath(f"//cuboid[name='{cuboid}']/size/z/text()")[0]) * 1000
        native = float(properties(record)["substrateThicknessA2"])
        assert math.isclose(thickness, native, abs_tol=1e-12)
        results.append(
            {
                "template": template,
                "branch": record["wizard"],
                "preset": preset,
                "thickness_mm": native,
                "archive": str(directory.relative_to(ROOT)),
            }
        )
    return results


def production_differences(records: list[dict]) -> list[dict]:
    definition = definitions()["wirebond_pbga"]
    differences = []
    for record in records:
        if record["family"] != "pbga_wb":
            continue
        values = properties(record)
        request = TemplateRequest(
            template_id="wirebond_pbga",
            overrides={"wirebond_pbga.footprint.size": record["preset"]},
        )
        adapted = definition.validate_request(request)
        for field, native_name in (
            ("substrate.thickness", "substrateThicknessA2"),
            ("bond_wire.total", "numberOfBondWiresNw"),
            ("vias.pitch", "viaPitchEv"),
        ):
            current, native = adapted.number(field), float(values[native_name])
            if not math.isclose(current, native, abs_tol=1e-12):
                differences.append(
                    {
                        "preset": record["preset"],
                        "field": field,
                        "packstudio": current,
                        "pack_native": native,
                    }
                )
    return differences


def main() -> None:
    records = json.loads((DIRECTORY / "native_defaults.json").read_text())["records"]
    four_layer = json.loads((DIRECTORY / "native_defaults_4layer.json").read_text())["records"]
    assert len(records) == 342 and len(four_layer) == 74
    assert len({(r["family"], r["preset"]) for r in records}) == len(records)
    differences = production_differences(records)
    props = [p for r in records for g in r["groups"] for p in g["properties"]]
    report = {
        "default_record_count": len(records),
        "four_layer_record_count": len(four_layer),
        "families": dict(Counter(r["family"] for r in records)),
        "native_property_states": dict(Counter(p["native_state"] for p in props)),
        "populated_property_instances": sum(p["value"] is not None for p in props),
        "unset_property_instances": sum(p["value"] is None for p in props),
        **source_audit(records),
        **rule_audit(records, four_layer),
        "archived_floxml_cross_checks": xml_audit(records, four_layer),
        "production_comparison_scope": "36 wirebond PBGA presets, three numeric fields only",
        "production_difference_count": len(differences),
        "production_difference_fields": dict(Counter(d["field"] for d in differences)),
        "production_differences": differences,
        "complete_for_all_options": False,
    }
    (DIRECTORY / "native_defaults_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key not in {"production_differences", "archived_floxml_cross_checks"}
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
