"""Capture native non-discrete solder-ball geometry and constituent material probes."""

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.csv_solder_ball_probes import MAP_ROWS, saved_map, write_input
from tools.floxml_validation.native import replay
from tools.floxml_validation.native_suite import read_des
from tools.solder_ball_array_probes import ROOT

DEFAULT_OUTPUT = ROOT / "flotherm_pack_data/validation/equivalent_solder_balls_2026-10-25-verified"
PROFILES = {
    "pbga_wb_ortho": ("pbga_wb", "orthotropicCuboid"),
    "pbga_wb_iso": ("pbga_wb", "isotropicCuboid"),
    "pbga_fc_ortho": ("pbga_fc", "orthotropicCuboid"),
    "cbga_fc_ortho": ("cbga_fc", "orthotropicCuboid"),
}


def definitions():
    cases = []

    def add(identifier, rows=(), **changes):
        values = {
            "MD": "5",
            "ME": "5",
            "e": "0.8",
            "b": "0.5",
            "A1": "0.4",
            "csvBGA": "UNCHECKED",
            "balls": "",
            "depop_center": "UNCHECKED",
            "MDp": "2",
            "MEp": "2",
            "staggered_matrix": "UNCHECKED",
            "central_balls": "UNCHECKED",
            "MDc": "2",
            "MEc": "2",
            "central_staggered_matrix": "UNCHECKED",
            "k_solder": "Solder (Sn63/Pb37)",
        }
        values.update({k: str(v) for k, v in changes.items()})
        cases.append({"id": identifier, "des_changes": values, "map_rows": rows})

    add("regular55")
    add("regular46", MD=4, ME=6)
    add("stagger55", staggered_matrix="CHECKED")
    add("stagger46", MD=4, ME=6, staggered_matrix="CHECKED")
    for px, py in ((1, 1), (2, 2), (3, 3), (1, 3), (3, 1), (2, 4), (4, 2), (5, 5), (5, 2), (2, 5)):
        add(f"depop{px}{py}", depop_center="CHECKED", MDp=px, MEp=py)
    add("depop65_22", MD=6, ME=5, depop_center="CHECKED")
    add("depop65_33", MD=6, ME=5, depop_center="CHECKED", MDp=3, MEp=3)
    add("stagger_depop22", depop_center="CHECKED", staggered_matrix="CHECKED")
    all_cells = {(i, j) for i in range(5) for j in range(5)}
    perimeter = {(i, j) for i, j in all_cells if i in (0, 4) or j in (0, 4)}
    corner_removed = ":".join(f"{i}x{j}" for i, j in sorted(all_cells - {(0, 0)}))
    add("explicit24", balls=corner_removed)
    add("explicit1", balls="0x0")
    add("explicit_perimeter", balls=":".join(f"{i}x{j}" for i, j in sorted(perimeter)))
    add("explicit24_depop22", balls=corner_removed, depop_center="CHECKED")
    add("explicit24_center", balls=corner_removed, central_balls="CHECKED")
    add("center22", central_balls="CHECKED")
    add("center33", central_balls="CHECKED", MDc=3, MEc=3)
    add(
        "center33_stagger",
        central_balls="CHECKED",
        MDc=3,
        MEc=3,
        central_staggered_matrix="CHECKED",
    )
    add("depop_center_restore", central_balls="CHECKED", MDc=3, MEc=3, depop_center="CHECKED")
    add("csv3", rows=MAP_ROWS, csvBGA="CHECKED")
    add(
        "csv3_all_filters",
        rows=MAP_ROWS,
        csvBGA="CHECKED",
        balls="0x0",
        staggered_matrix="CHECKED",
        depop_center="CHECKED",
        central_balls="CHECKED",
    )
    add("csv_empty", csvBGA="CHECKED")
    add("diameter04", b=0.4)
    add("pitch11", e=1.1)
    add("height05", A1=0.5)
    add("solder_pb90", k_solder="Solder (Pb90/Sn10)")
    add("single_column", MD=1, ME=5)
    return cases


def capture(installation, output):
    if output.exists():
        raise ValueError("capture directory exists; choose a new directory")
    output.mkdir(parents=True)
    baselines = []
    for identifier, (family, mode) in PROFILES.items():
        root = ET.parse(
            ROOT / f"flotherm_pack_data/templates/{family}/baseline/script.xml"
        ).getroot()
        commands = [ET.tostring(e, encoding="unicode") for e in root if e.tag == "new_package"]
        commands.append(
            ET.tostring(
                ET.Element(
                    "modify_component",
                    name="modelingOptions",
                    property_name="modelSolderBallArrayAs",
                    new_value=mode,
                ),
                encoding="unicode",
            )
        )
        baselines.append({"id": identifier, "commands": commands})
    result = replay(installation, baselines, output / "baselines")
    if result["exit_code"] != 0 or result["errors"] or len(result["exports"]) != len(PROFILES):
        raise RuntimeError(f"baseline capture failed: {result}")
    for identifier, (family, mode) in PROFILES.items():
        directory = output / identifier
        inputs = directory / "inputs"
        inputs.mkdir(parents=True)
        baseline_path = output / "baselines" / f"{identifier}.des"
        baseline = read_des(baseline_path)
        cases = definitions()
        for case in cases:
            case["des_changes"]["radio_BGA_modeling"] = baseline["radio_BGA_modeling"]
            path = inputs / f"{case['id']}.des"
            write_input(path, baseline_path, baseline | case["des_changes"], case["map_rows"])
            case["commands"] = [
                ET.tostring(ET.Element("load_des", filename=str(path)), encoding="unicode")
            ]
        manifest = {"family": family, "mode": mode, "cases": cases}
        (directory / "definitions.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        result = replay(installation, cases, directory / "native")
        if result["exit_code"] != 0 or result["errors"] or len(result["exports"]) != len(cases):
            raise RuntimeError(f"capture failed: {identifier}: {result}")
        for case in cases:
            saved = directory / "native" / f"{case['id']}.des"
            readback = read_des(saved)
            fallback = (
                bool(case["des_changes"]["balls"]) or case["des_changes"]["csvBGA"] == "CHECKED"
            )
            expected = case["des_changes"] | ({"radio_BGA_modeling": "3"} if fallback else {})
            assert all(readback.get(k) == v for k, v in expected.items())
            assert saved_map(saved) == list(map(tuple, case["map_rows"]))
        reload_cases = [
            {
                "id": case["id"],
                "commands": [
                    ET.tostring(
                        ET.Element(
                            "load_des", filename=str(directory / "native" / f"{case['id']}.des")
                        ),
                        encoding="unicode",
                    )
                ],
            }
            for case in cases
            if case["des_changes"]["balls"] or case["des_changes"]["csvBGA"] == "CHECKED"
        ]
        result = replay(installation, reload_cases, directory / "reloaded")
        if (
            result["exit_code"] != 0
            or result["errors"]
            or len(result["exports"]) != len(reload_cases)
        ):
            raise RuntimeError(f"saved-file reload failed: {identifier}: {result}")
        print(
            json.dumps(
                {
                    "profile": identifier,
                    "captured": len(cases),
                    "reloaded": len(reload_cases),
                    "mode_code": baseline["radio_BGA_modeling"],
                }
            ),
            flush=True,
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    capture(args.installation.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
