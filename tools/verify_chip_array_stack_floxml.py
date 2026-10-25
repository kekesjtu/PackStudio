"""Verify native Chip Array via placement, materials, and metal layer geometry."""

import argparse
import json
import math
from pathlib import Path

from tools.chip_array_stack_probes import DEFAULT_OUTPUT
from tools.floxml_validation.native import fingerprint
from tools.floxml_validation.native_suite import read_des
from tools.floxml_validation.reader import read
from tools.verify_wb_via_stack_floxml import compare_tree, near


def mixture(first, second, fraction):
    density = fraction * first[3] + (1 - fraction) * second[3]
    heat = (fraction * first[3] * first[4] + (1 - fraction) * second[3] * second[4]) / density
    return [
        *(fraction * a + (1 - fraction) * b for a, b in zip(first[:3], second[:3], strict=True)),
        density,
        heat,
    ]


def layer_rows(values, count):
    rows = []
    for index in range(count):
        suffix = f"a{index + 1}" if count == 2 else str(index + 1)
        thickness = float(values[f"tz{suffix}"])
        depth = (
            0
            if index == 0
            else (
                float(values["A2"]) - thickness
                if index == count - 1
                else float(values[f"z{index + 1}"])
            )
        )
        rows.append(
            dict(depth=depth, thickness=thickness, coverage=float(values[f"coverage{suffix}"]))
        )
    return rows


def observe(directory, case):
    path = directory / f"{case['id']}.xml"
    saved = path.with_suffix(".des")
    values, document = read_des(saved), read(path)
    for key, expected in case.get("des_changes", {}).items():
        near(float(values[key]), float(expected))
    a1, a2 = float(values["A1"]), float(values["A2"])
    near(a1, case["a1"])
    near(a2, case["a2"])
    rows = layer_rows(values, case["layers"])
    near(rows[0]["thickness"], case["top"])
    near(rows[-1]["thickness"], case["bottom"])
    if case["layers"] == 4 and a2 == 0.56 and "des_changes" not in case:
        gap = (a2 - case["top"] - case["bottom"] - 2 * 0.036) / 3
        near(rows[1]["depth"], case["top"] + gap)
        near(rows[2]["depth"], case["top"] + 2 * gap)
    near(int(values["radio_Via_modeling"]), 5 if case["mode"] == "accurate" else 3)
    near(int(values["radio_filled_vias"]), 1 if case["filled"] else 2)
    metal = [385, 385, 385, 8930, 385]
    air = [0.0261, 0.0261, 0.0261, 1.1614, 1007]
    substrate = [0.2, 0.2, 0.2, 1900, 921]
    assert values["k_metal"] == "Copper (Pure)" and values["k_substr"] == "BT"
    compare_tree(list(document.materials["BT"]), list(map(float, substrate)))
    traces = [b for b in document.boxes if b.name.startswith("trace_")]
    assert len(traces) == case["layers"]
    metals = []
    for index, row in enumerate(rows):
        block = next(b for b in traces if b.name == f"trace_{index}")
        expected_origin = (
            -float(values["D"]) / 2,
            -float(values["E"]) / 2,
            a1 + a2 - row["depth"] - row["thickness"],
        )
        for actual, expected in zip(block.origin, expected_origin, strict=True):
            near(actual, expected)
        for actual, expected in zip(
            block.size, (float(values["D"]), float(values["E"]), row["thickness"]), strict=True
        ):
            near(actual, expected)
        properties = list(document.materials[block.material])
        compare_tree(properties, mixture(metal, substrate, row["coverage"] / 100))
        metals.append(
            row
            | {
                "name": block.name,
                "zmin": block.origin[2],
                "zmax": block.high[2],
                "properties": properties,
            }
        )

    vias = [b for b in document.boxes if b.name.startswith("thermal_via_")]
    nx, ny, pitch = int(values["MD"]), int(values["ME"]), float(values["e"])
    assert len(vias) == nx * ny
    diameter, plating, ball_diameter = (float(values[k]) for k in ("dv", "tpl", "b"))
    fraction = 1 if case["filled"] else 1 - ((diameter - 2 * plating) / diameter) ** 2
    properties = mixture(metal, air, fraction)
    approximate = case["mode"] == "approximate"
    if approximate:
        properties = mixture(properties, substrate, (diameter / ball_diameter) ** 2)
    side = math.sqrt(math.pi) * (ball_diameter if approximate else diameter) / 2
    offset_x, offset_y = (0, 0) if approximate else (float(values["vxoff"]), float(values["vyoff"]))
    actual_centers = set()
    for block in vias:
        for size, expected in zip(
            block.size, (side, side, a2 - case["top"] - case["bottom"]), strict=True
        ):
            near(size, expected)
        near(block.origin[2], a1 + case["bottom"])
        compare_tree(list(document.materials[block.material]), properties)
        actual_centers.add(
            (round(block.origin[0] + side / 2, 9), round(block.origin[1] + side / 2, 9))
        )
    expected_centers = {
        (
            round((i - (nx - 1) / 2) * pitch + offset_x, 9),
            round((j - (ny - 1) / 2) * pitch + offset_y, 9),
        )
        for i in range(nx)
        for j in range(ny)
    }
    assert actual_centers == expected_centers
    holes = [b for b in document.boxes if b.name == "top trace hole"]
    assert len(holes) == int(case["id"].endswith("top_hole"))
    hole_records = []
    for hole in holes:
        for actual, expected in zip(hole.size, (1.4, 1.0, case["top"]), strict=True):
            near(actual, expected)
        for actual, expected in zip(hole.origin, (-0.7, -0.5, metals[0]["zmin"]), strict=True):
            near(actual, expected)
        assert hole.material == values["k_ml"] == "Alloy-42"
        near(float(values["Lml"]), 1.4)
        near(float(values["Wml"]), 1)
        hole_records.append(
            {"origin": list(hole.origin), "size": list(hole.size), "material": hole.material}
        )
    via = vias[0]
    return {
        "id": case["id"],
        "layers": case["layers"],
        "mode": case["mode"],
        "filled": case["filled"],
        "input_mm": dict(A1=a1, A2=a2, top=case["top"], bottom=case["bottom"]),
        "via_count": len(vias),
        "via_side_mm": side,
        "via_zmin_mm": via.origin[2],
        "via_height_mm": via.size[2],
        "via_zmax_mm": via.high[2],
        "bottom_clearance_mm": via.origin[2] - metals[-1]["zmax"],
        "top_clearance_mm": metals[0]["zmin"] - via.high[2],
        "via_material": properties,
        "metal_rows": metals,
        "holes": hole_records,
        "centers_xy_mm": sorted(map(list, actual_centers)),
        "source_sha256": {"floxml": fingerprint(path), "des": fingerprint(saved)},
    }


def verify(output):
    cases = json.loads((output / "definitions.json").read_text(encoding="utf-8"))
    extra = json.loads((output / "metal-definitions.json").read_text(encoding="utf-8"))
    result = {"runs": {}, "cases": []}
    for phase, definitions in [("native", cases), ("metals", extra), ("reload", cases + extra)]:
        directory = output / phase
        run = json.loads((directory / "run.json").read_text(encoding="utf-8-sig"))
        assert run["exit_code"] == 0 and not run["errors"]
        assert set(run["exports"]) == {case["id"] for case in definitions}
        assert run["script_sha256"] == fingerprint(directory / "replay.xml")
        assert run["launcher_sha256"] == fingerprint(directory / "replay_wb_via_stack.ps1")
        for case in definitions:
            assert run["exports"][case["id"]] == fingerprint(directory / f"{case['id']}.xml")
        result["runs"][phase] = run
    for case in cases + extra:
        phase = "metals" if "des_changes" in case else "native"
        first, second = observe(output / phase, case), observe(output / "reload", case)
        difference = max(
            compare_tree(first[k], second[k]) for k in first.keys() - {"source_sha256"}
        )
        near(first["bottom_clearance_mm"], 0)
        near(first["top_clearance_mm"], 0)
        first["max_reload_numeric_difference"] = difference
        first["reload_sha256"] = second["source_sha256"]
        result["cases"].append(first)
    result["conclusion"] = {
        "zmin": "A1 + t_bottom",
        "height": "A2 - t_top - t_bottom",
        "zmax": "A1 + A2 - t_top",
        "outer_layer_offset_mm": 0,
        "fresh_stack_cases": len(cases),
        "metal_table_cases": len(extra),
        "reload_cases": len(cases + extra),
        "passed": True,
    }
    (output / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["conclusion"], indent=2))
    for case in result["cases"]:
        print(
            f"{case['id']}: z={case['via_zmin_mm']:.6f}..{case['via_zmax_mm']:.6f}, "
            f"h={case['via_height_mm']:.6f}, gaps="
            f"{case['bottom_clearance_mm']:.6f}/{case['top_clearance_mm']:.6f}"
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    verify(args.output.resolve())


if __name__ == "__main__":
    main()
