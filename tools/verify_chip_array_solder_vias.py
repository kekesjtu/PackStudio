"""Check native Chip Array solder filters against Via cells, geometry and materials."""

import argparse
import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.chip_array_solder_via_probes import DEFAULT_OUTPUT, PROFILES
from tools.csv_solder_ball_probes import saved_map
from tools.floxml_validation.native import fingerprint
from tools.floxml_validation.native_suite import read_des
from tools.floxml_validation.reader import read
from tools.verify_chip_array_stack_floxml import mixture
from tools.verify_solder_ball_arrays_floxml import (
    compare_group,
    expected_positions,
    predicted_cells,
)
from tools.verify_wb_via_stack_floxml import compare_tree, near


def observe(directory, case, layers, requested_mode):
    xml = directory / f"{case['id']}.xml"
    saved = xml.with_suffix(".des")
    values = read_des(saved)
    changes = {}
    for key, expected in case["des_changes"].items():
        if values.get(key) != expected:
            try:
                near(float(values[key]), float(expected))
            except (ValueError, KeyError, AssertionError):
                changes[key] = {"requested": expected, "saved": values.get(key)}
    assert not (changes.keys() - {"radio_Via_modeling"}), changes
    rows = saved_map(saved)
    expected_rows = [(name, round(x, 6), round(y, 6)) for name, x, y in case["map_rows"]]
    assert rows == expected_rows
    root = ET.parse(xml).getroot()
    grid, central = predicted_cells(values)
    nx, ny, pitch = int(values["MD"]), int(values["ME"]), float(values["e"])
    grid_main = expected_positions(grid, nx, ny, pitch, "solder_ball")
    if values["csvBGA"] == "CHECKED":
        expected_main = {name: (x, y) for name, x, y in rows}
        expected_center = {}
    else:
        expected_main = grid_main
        expected_center = expected_positions(
            central, int(values["MDc"]), int(values["MEc"]), pitch, "center_sball"
        )
    main = compare_group(root, "Solder_ball", expected_main, values)
    center = compare_group(root, "Center_SBall", expected_center, values)
    document = read(xml)
    vias = [block for block in document.boxes if block.name.startswith("thermal_via_")]
    names = expected_positions(grid, nx, ny, pitch, "thermal_via")
    assert {block.name for block in vias} == set(names)
    mode = int(values["radio_Via_modeling"])
    assert mode in (3, 5)
    approximate = mode == 3
    diameter, ball_diameter, plating = (float(values[key]) for key in ("dv", "b", "tpl"))
    fraction = 1 - ((diameter - 2 * plating) / diameter) ** 2
    metal, air = [385, 385, 385, 8930, 385], [0.0261, 0.0261, 0.0261, 1.1614, 1007]
    properties = mixture(metal, air, fraction)
    if approximate:
        properties = mixture(
            properties, [0.2, 0.2, 0.2, 1900, 921], (diameter / ball_diameter) ** 2
        )
    side = math.sqrt(math.pi) * (ball_diameter if approximate else diameter) / 2
    offset = (0, 0) if approximate else (float(values["vxoff"]), float(values["vyoff"]))
    top_key, bottom_key = ("tza1", "tza2") if layers == 2 else ("tz1", "tz4")
    a1, a2 = float(values["A1"]), float(values["A2"])
    top, bottom = float(values[top_key]), float(values[bottom_key])
    near(a2, 0.36 if layers == 2 else 0.56)
    observations = []
    for block in sorted(vias, key=lambda item: item.name):
        target = names[block.name]
        for actual, expected in zip(block.size, (side, side, a2 - top - bottom), strict=True):
            near(actual, expected)
        near(block.origin[2], a1 + bottom)
        center_xy = [block.origin[n] + block.size[n] / 2 for n in (0, 1)]
        for actual, center_value, shift in zip(center_xy, target, offset, strict=True):
            near(actual, center_value + shift)
        compare_tree(list(document.materials[block.material]), properties)
        observations.append(
            {
                "name": block.name,
                "center_xy_mm": center_xy,
                "origin_mm": list(block.origin),
                "size_mm": list(block.size),
            }
        )
    material_ids = {block.material for block in vias}
    assert len(material_ids) <= 1
    material = list(document.materials[next(iter(material_ids))]) if material_ids else None
    return {
        "id": case["id"],
        "layers": layers,
        "requested_mode": requested_mode,
        "saved_mode": mode,
        "native_input_changes": changes,
        "csv_enabled": values["csvBGA"] == "CHECKED",
        "map_rows": list(map(list, rows)),
        "main_ball_count": main["count"],
        "center_ball_count": center["count"],
        "total_ball_count": main["count"] + center["count"],
        "main_centers_xy_mm": main["centers_xy_mm"],
        "center_centers_xy_mm": center["centers_xy_mm"],
        "via_count": len(vias),
        "via_cells": sorted(map(list, grid)),
        "via_material": material,
        "via_side_mm": side,
        "via_zmin_mm": a1 + bottom,
        "via_height_mm": a2 - top - bottom,
        "vias": observations,
        "sha256": {"xml": fingerprint(xml), "des": fingerprint(saved)},
    }


def verify(output):
    result = {"profiles": {}}
    for profile, (layers, mode) in PROFILES.items():
        directory = output / profile
        cases = json.loads((directory / "definitions.json").read_text(encoding="utf-8"))
        runs = {}
        for phase in ("native", "reload"):
            run_path = directory / phase / "run.json"
            run = json.loads(run_path.read_text(encoding="utf-8-sig"))
            assert run["exit_code"] == 0 and not run["errors"]
            assert set(run["exports"]) == {case["id"] for case in cases}
            assert run["script_sha256"] == fingerprint(run_path.parent / "replay.xml")
            assert run["launcher_sha256"] == fingerprint(
                run_path.parent / "replay_wb_via_stack.ps1"
            )
            for case in cases:
                assert run["exports"][case["id"]] == fingerprint(
                    run_path.parent / f"{case['id']}.xml"
                )
            runs[phase] = run
        observations = []
        for case in cases:
            first = observe(directory / "native", case, layers, mode)
            second = observe(directory / "reload", case, layers, mode)
            difference = max(
                compare_tree(first[key], second[key]) for key in first.keys() - {"sha256"}
            )
            source = directory / "inputs" / f"{case['id']}.des"
            original = read_des(source)
            assert all(original[key] == value for key, value in case["des_changes"].items())
            first["input_sha256"] = fingerprint(source)
            first["reload_sha256"] = second["sha256"]
            first["max_reload_numeric_difference"] = difference
            observations.append(first)
        reference = next(case for case in observations if case["id"] == "full55")
        for case in observations:
            if case["via_count"] and case["id"] != "diameter04":
                compare_tree(case["via_material"], reference["via_material"])
        result["profiles"][profile] = {"runs": runs, "cases": observations}
        print(f"{profile}: {len(observations)} cases passed", flush=True)
    groups = list(result["profiles"].values())
    for first, other in zip(groups[:-1], groups[1:], strict=True):
        for case, candidate in zip(first["cases"], other["cases"], strict=True):
            assert case["id"] == candidate["id"]
            for key in ("main_ball_count", "center_ball_count", "via_count", "via_cells"):
                assert case[key] == candidate[key]
    result["summary"] = {
        "profiles": len(PROFILES),
        "cases_per_profile": len(groups[0]["cases"]),
        "fresh_exports": sum(len(group["cases"]) for group in groups),
        "reload_exports": sum(len(group["cases"]) for group in groups),
        "all_passed": True,
    }
    (output / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    for case in groups[0]["cases"]:
        print(
            f"{case['id']}: solder={case['main_ball_count']}+{case['center_ball_count']} "
            f"vias={case['via_count']}"
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    verify(args.output.resolve())


if __name__ == "__main__":
    main()
