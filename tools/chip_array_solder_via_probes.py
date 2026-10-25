"""Prepare native Chip Array solder-removal/Via coupling experiments."""

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.chip_array_stack_probes import DEFAULT_OUTPUT as STACK_OUTPUT
from tools.chip_array_stack_probes import definitions as stack_definitions
from tools.csv_solder_ball_probes import MAP_ROWS, write_input
from tools.floxml_validation.native import fingerprint
from tools.floxml_validation.native_suite import read_des
from tools.verify_wb_via_stack_floxml import prepare_replay

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "flotherm_pack_data/validation/chip_array_solder_via_2026-10-25"
PROFILES = {
    "l2_accurate": (2, 5),
    "l2_approximate": (2, 3),
    "l4_accurate": (4, 5),
    "l4_approximate": (4, 3),
}


def definitions(mode):
    cases = []

    def add(identifier, rows=(), **changes):
        values = {
            "MD": "5",
            "ME": "5",
            "e": "0.8",
            "b": "0.46",
            "A1": "0.4",
            "balls": "",
            "depop_center": "UNCHECKED",
            "MDp": "2",
            "MEp": "2",
            "staggered_matrix": "UNCHECKED",
            "central_balls": "UNCHECKED",
            "central_staggered_matrix": "UNCHECKED",
            "MDc": "2",
            "MEc": "2",
            "csvBGA": "UNCHECKED",
            "radio_Via_modeling": str(mode),
        }
        values.update({key: str(value) for key, value in changes.items()})
        cases.append({"id": identifier, "des_changes": values, "map_rows": rows})

    add("full55")
    add("grid46", MD=4, ME=6)
    add("stagger55", staggered_matrix="CHECKED")
    add("stagger46", MD=4, ME=6, staggered_matrix="CHECKED")
    for px, py in ((1, 1), (2, 2), (3, 3), (1, 2), (5, 2)):
        add(f"depop{px}{py}", depop_center="CHECKED", MDp=px, MEp=py)
    add("stagger_depop22", depop_center="CHECKED", staggered_matrix="CHECKED")
    all_cells = {(i, j) for i in range(5) for j in range(5)}
    explicit = ":".join(f"{i}x{j}" for i, j in sorted(all_cells - {(0, 0)}))
    perimeter = ":".join(f"{i}x{j}" for i, j in sorted(all_cells) if i in (0, 4) or j in (0, 4))
    add("explicit24", balls=explicit)
    add("explicit1", balls="0x0")
    add("explicit24_stagger", balls=explicit, staggered_matrix="CHECKED")
    add("explicit24_depop", balls=explicit, depop_center="CHECKED")
    add("explicit_perimeter_center33", balls=perimeter, central_balls="CHECKED", MDc=3, MEc=3)
    add("central22", central_balls="CHECKED")
    add("central33", central_balls="CHECKED", MDc=3, MEc=3)
    add(
        "central33_stagger",
        central_balls="CHECKED",
        MDc=3,
        MEc=3,
        central_staggered_matrix="CHECKED",
    )
    add("depop_center_restore", depop_center="CHECKED", central_balls="CHECKED", MDc=3, MEc=3)
    add("csv3", rows=MAP_ROWS, csvBGA="CHECKED")
    add("csv3_stagger", rows=MAP_ROWS, csvBGA="CHECKED", staggered_matrix="CHECKED")
    add("csv3_depop", rows=MAP_ROWS, csvBGA="CHECKED", depop_center="CHECKED")
    add("csv3_explicit1", rows=MAP_ROWS, csvBGA="CHECKED", balls="0x0")
    add(
        "csv3_all",
        rows=MAP_ROWS,
        csvBGA="CHECKED",
        balls="0x0",
        depop_center="CHECKED",
        staggered_matrix="CHECKED",
        central_balls="CHECKED",
    )
    add("csv_empty", csvBGA="CHECKED")
    add("csv_disabled", rows=MAP_ROWS)
    add("csv_duplicates", rows=[("D1", 0.25, -0.7), ("D2", 0.25, -0.7)], csvBGA="CHECKED")
    add("csv_translated", rows=[(n, x + 0.35, y - 0.4) for n, x, y in MAP_ROWS], csvBGA="CHECKED")
    add("diameter04", b=0.4)
    add("pitch065", e=0.65)
    add("height05", A1=0.5)
    return cases


def load_command(path):
    return ET.tostring(ET.Element("load_des", filename=str(path)), encoding="unicode")


def prepare(installation, output, phase):
    if phase == "native":
        if output.exists():
            raise ValueError("use a new capture directory")
        output.mkdir(parents=True)
        sources = {
            c["layers"]: STACK_OUTPUT / "native" / f"{c['id']}.des"
            for c in stack_definitions()
            if c["top"] == c["bottom"] == 0.018
        }
        (output / "baseline-sources.json").write_text(
            json.dumps(
                {
                    str(layer): {"path": str(path), "sha256": fingerprint(path)}
                    for layer, path in sources.items()
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    for profile, (layers, mode) in PROFILES.items():
        directory = output / profile
        members = []
        if phase == "native":
            inputs = directory / "inputs"
            inputs.mkdir(parents=True)
            baseline = sources[layers]
            initial = read_des(baseline)
            cases = definitions(mode)
            for case in cases:
                path = inputs / f"{case['id']}.des"
                write_input(path, baseline, initial | case["des_changes"], case["map_rows"])
                members.append({"id": case["id"], "commands": [load_command(path)]})
            (directory / "definitions.json").write_text(
                json.dumps(cases, indent=2), encoding="utf-8"
            )
        else:
            cases = json.loads((directory / "definitions.json").read_text(encoding="utf-8"))
            run = json.loads((directory / "native/run.json").read_text(encoding="utf-8-sig"))
            assert run["exit_code"] == 0 and not run["errors"]
            assert set(run["exports"]) == {case["id"] for case in cases}
            for case in cases:
                path = directory / "native" / f"{case['id']}.des"
                read_des(path)
                members.append({"id": case["id"], "commands": [load_command(path)]})
        prepare_replay(installation, members, directory / phase)
        print(f"Prepared {profile}/{phase}: {len(members)} cases", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--prepare", choices=("native", "reload"), required=True)
    args = parser.parse_args()
    prepare(args.installation.resolve(), args.output.resolve(), args.prepare)


if __name__ == "__main__":
    main()
