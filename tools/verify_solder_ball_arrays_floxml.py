"""Verify physical solder-ball positions from four families' discrete native FloXML."""

import argparse
import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.floxml_validation.native_suite import read_des
from tools.infer_chip_array_bond_wires_floxml import provenance
from tools.solder_ball_array_probes import DEFAULT_OUTPUT, FAMILIES, ROOT


def predicted_cells(values):
    md, me = int(values["MD"]), int(values["ME"])
    if values["balls"]:
        # Explicit DES cells count rows down from the upper edge of the grid.
        cells = [
            (int(s.split("x")[0]), me - 1 - int(s.split("x")[1]))
            for s in values["balls"].split(":")
        ]
    else:
        cells = [(i, j) for i in range(md) for j in range(me)]
        if values["depop_center"] == "CHECKED":
            px, py = int(values["MDp"]), int(values["MEp"])
            if px < md and py < me:
                cells = [
                    (i, j)
                    for i, j in cells
                    if i < px // 2 or i >= md - px // 2 or j < py // 2 or j >= me - py // 2
                ]
        if values["staggered_matrix"] == "CHECKED":
            cells = [(i, j) for i, j in cells if (i + j) % 2 == 0]
    center = []
    if values["central_balls"] == "CHECKED":
        center = [(i, j) for i in range(int(values["MDc"])) for j in range(int(values["MEc"]))]
        if values["central_staggered_matrix"] == "CHECKED":
            center = [(i, j) for i, j in center if (i + j) % 2 == 0]
    return cells, center


def expected_positions(cells, columns, rows, pitch, prefix):
    return {
        f"{prefix}_{i + 1}_{j + 1}": ((i - (columns - 1) / 2) * pitch, (j - (rows - 1) / 2) * pitch)
        for i, j in cells
    }


def compare_group(root, group_name, expected, values):
    group = next(
        (a for a in root.findall("./geometry/assembly") if a.findtext("name") == group_name), None
    )
    elements = [] if group is None else group.findall("./geometry/cuboid")
    assert set(e.findtext("name") for e in elements) == set(expected), group_name
    if group is not None:
        assert all(float(group.findtext(f"position/{axis}")) == 0 for axis in "xyz")
    side = math.sqrt(math.pi) * float(values["b"]) / 2
    height = float(values["A1"])
    errors, centers = [], []
    for element in elements:
        sizes = [float(element.findtext(f"size/{axis}")) * 1000 for axis in "xyz"]
        origin = [float(element.findtext(f"position/{axis}")) * 1000 for axis in "xyz"]
        center = [origin[n] + sizes[n] / 2 for n in range(2)]
        target = expected[element.findtext("name")]
        errors.extend(abs(a - b) for a, b in zip(center, target, strict=True))
        errors.extend(abs(a - b) for a, b in zip(sizes, (side, side, height), strict=True))
        errors.append(abs(origin[2]))
        assert element.findtext("material") == values["k_solder"]
        centers.append(tuple(round(v, 10) for v in center))
    error = max(errors, default=0)
    assert error < 1e-10, (group_name, error)
    return {"count": len(elements), "centers_xy_mm": sorted(centers), "max_error_mm": error}


def verify_case(directory, definition):
    identifier = definition["id"]
    xml = directory / "native" / f"{identifier}.xml"
    saved = xml.with_suffix(".des")
    values = read_des(saved)
    assert all(values.get(k) == v for k, v in definition["des_changes"].items())
    root = ET.parse(xml).getroot()
    cells, central_cells = predicted_cells(values)
    pitch = float(values["e"])
    main_expected = expected_positions(
        cells, int(values["MD"]), int(values["ME"]), pitch, "solder_ball"
    )
    central_expected = expected_positions(
        central_cells, int(values["MDc"]), int(values["MEc"]), pitch, "center_sball"
    )
    main = compare_group(root, "Solder_ball", main_expected, values)
    center = compare_group(root, "Center_SBall", central_expected, values)
    main_sites = set(map(tuple, main["centers_xy_mm"]))
    center_sites = set(map(tuple, center["centers_xy_mm"]))
    return {
        "id": identifier,
        "sources": [
            provenance(xml),
            provenance(saved),
            provenance(directory / "inputs" / f"{identifier}.des"),
        ],
        "inputs": {k: values[k] for k in definition["des_changes"]},
        "main": main,
        "center": center,
        "entity_count": main["count"] + center["count"],
        "unique_center_count": len(main_sites | center_sites),
        "coincident_center_count": len(main_sites & center_sites),
        "passed": True,
    }


def verify(archive, output):
    baseline_run_path = archive / "baselines/run.json"
    baseline_run = json.loads(baseline_run_path.read_text(encoding="utf-8"))
    assert baseline_run["exit_code"] == 0 and not baseline_run["errors"]
    assert set(baseline_run["exports"]) == set(FAMILIES)
    for family, digest in baseline_run["exports"].items():
        assert provenance(archive / "baselines" / f"{family}.xml")["sha256"] == digest
    families = {}
    for family in FAMILIES:
        directory = archive / family
        definitions_file = directory / "definitions.json"
        definitions = json.loads(definitions_file.read_text(encoding="utf-8"))
        run_file = directory / "native/run.json"
        run = json.loads(run_file.read_text(encoding="utf-8"))
        assert run["exit_code"] == 0 and not run["errors"]
        assert len(run["exports"]) == len(definitions)
        for identifier, digest in run["exports"].items():
            assert provenance(directory / "native" / f"{identifier}.xml")["sha256"] == digest
        cases = [verify_case(directory, definition) for definition in definitions]
        families[family] = {
            "sources": [
                provenance(definitions_file),
                provenance(run_file),
                provenance(directory / "native/replay.xml"),
            ],
            "native_execution": run,
            "cases": cases,
            "summary": {
                "cases": len(cases),
                "passed": all(c["passed"] for c in cases),
                "max_error_mm": max(
                    max(c["main"]["max_error_mm"], c["center"]["max_error_mm"]) for c in cases
                ),
            },
        }
    by_family = {family: {c["id"]: c for c in item["cases"]} for family, item in families.items()}
    reference = by_family["chip_array"]
    for family in FAMILIES[1:]:
        for identifier, case in by_family[family].items():
            for group in ("main", "center"):
                assert case[group]["centers_xy_mm"] == reference[identifier][group]["centers_xy_mm"]
    summary = {
        "family_count": len(families),
        "cases_per_family": len(reference),
        "new_discrete_exports": sum(item["summary"]["cases"] for item in families.values()),
        "new_baseline_exports": 4,
        "all_passed": True,
        "cross_family_positions_identical": True,
        "max_error_mm": max(item["summary"]["max_error_mm"] for item in families.values()),
    }
    report = {
        "date": "2026-10-25",
        "scope": "Actual discrete solder-ball geometry; no bond wires",
        "evidence": "Fresh native FloXML, input/saved DES, native exporter logs and hashes. "
        "No production geometry generator or DLL calculation probes used for verification.",
        "limitations": [
            "Regular-grid explicit cell lists are covered; nonempty arbitrary-coordinate "
            "CSV maps are not captured.",
            "Equivalent block materials are outside scope.",
        ],
        "summary": summary,
        "baseline_sources": [
            provenance(baseline_run_path),
            provenance(archive / "baselines/replay.xml"),
        ],
        "baseline_native_execution": baseline_run,
        "families": families,
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/validation/solder_ball_arrays_floxml_2026-10-25.json",
    )
    args = parser.parse_args()
    verify(args.archive.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
