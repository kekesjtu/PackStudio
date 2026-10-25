"""Capture explicit-cell and central-depopulation FloXML probes using PACK's exporter."""

import argparse
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.floxml_validation.native import replay
from tools.floxml_validation.native_suite import read_des

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT / "flotherm_pack_data/templates/chip_array/validation/ball_count_2026-10-25/suite"
)


def definitions():
    all_cells = {(x, y) for x in range(5) for y in range(5)}
    center = {(x, y) for x in range(1, 4) for y in range(1, 4)}
    cases = []
    specifications = [
        ("regular25", set(), False, None),
        ("remove_corner", {(0, 0)}, False, None),
        ("remove_two_corners", {(0, 0), (4, 4)}, False, None),
        ("remove_center_cell", {(2, 2)}, False, None),
        ("explicit_perimeter", center, False, None),
        ("central_only", set(), True, None),
        ("central_plus_corner", {(0, 0)}, True, None),
        ("central_plus_center_cell", {(2, 2)}, True, None),
        ("central_plus_crossing", {(0, 0), (2, 2)}, True, None),
        ("central_plus_precomputed_union", center | {(0, 0)}, True, None),
        ("central_plus_matching_list", center, True, None),
        ("central_plus_two_outer_corners", center | {(0, 0), (4, 4)}, True, None),
        ("independent_wire_count7", {(0, 0)}, False, 7),
    ]
    for identifier, removed, central, independent in specifications:
        explicit = sorted(all_cells - removed) if removed else []
        expected = (
            set(map(tuple, explicit)) if explicit else all_cells - (center if central else set())
        )
        count = independent if independent is not None else 16 if central else 25
        changes = {
            "balls": ":".join(f"{x}x{y}" for x, y in explicit),
            "depop_center": "CHECKED" if central else "UNCHECKED",
            "MDp": "2" if central else "5",
            "MEp": "2" if central else "5",
            "csvBGA": "UNCHECKED",
            "central_balls": "UNCHECKED",
            "staggered_matrix": "UNCHECKED",
            "radio_default_bwNumber": "1" if independent is None else "2",
        }
        if independent is not None:
            changes["Nw"] = str(independent)
        cases.append(
            {
                "id": identifier,
                "des_changes": changes,
                "removed_cells": sorted(removed),
                "explicit_kept_cells": explicit,
                "central_enabled": central,
                "independent_wire_count": independent,
                "expected_geometry_cells": sorted(expected),
                "candidate_rule_N": count,
                "union_hypothesis_count": len(all_cells - removed - (center if central else set())),
            }
        )
    return cases


def capture(installation, output):
    if output.exists():
        raise ValueError("capture target already exists; choose a new output directory")
    output.mkdir(parents=True)
    root = ET.parse(ROOT / "flotherm_pack_data/templates/chip_array/baseline/script.xml").getroot()
    commands = [ET.tostring(e, encoding="unicode") for e in root if e.tag == "new_package"]
    result = replay(installation, [{"id": "fresh", "commands": commands}], output / "baseline")
    if result["exit_code"] != 0 or result["errors"] or len(result["exports"]) != 1:
        raise RuntimeError(f"baseline export failed: {result}")
    baseline = read_des(output / "baseline/fresh.des")
    assert baseline["MD"] == baseline["ME"] == "5"
    cases = definitions()
    inputs = output / "inputs"
    inputs.mkdir()
    for case in cases:
        values = baseline | case["des_changes"]
        path = inputs / f"{case['id']}.des"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(path.name, "\n".join(f"{k}|{v}" for k, v in values.items()) + "\n")
        case["commands"] = [
            ET.tostring(ET.Element("load_des", filename=str(path)), encoding="unicode")
        ]
    result = replay(installation, cases, output / "native")
    if result["exit_code"] != 0 or result["errors"] or len(result["exports"]) != len(cases):
        raise RuntimeError(f"probe export failed: {result}")
    for case in cases:
        readback = read_des(output / "native" / f"{case['id']}.des")
        for key, value in case["des_changes"].items():
            if readback.get(key) != value:
                raise ValueError(f"PACK changed the intended input: {case['id']}/{key}")
    (output / "definitions.json").write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"cases_exported": len(cases), "output": str(output)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    capture(args.installation.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
