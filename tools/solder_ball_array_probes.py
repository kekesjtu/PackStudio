"""Capture discrete solder-ball arrays for all four PACK BGA package families."""

import argparse
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.floxml_validation.native import replay
from tools.floxml_validation.native_suite import read_des

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ("chip_array", "pbga_wb", "pbga_fc", "cbga_fc")
DEFAULT_OUTPUT = ROOT / "flotherm_pack_data/validation/solder_ball_arrays_2026-10-25-complete"


def definitions():
    items = []

    def add(identifier, **changes):
        values = {
            "MD": "5",
            "ME": "5",
            "e": "0.8",
            "b": "0.5",
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
        }
        values.update({k: str(v) for k, v in changes.items()})
        items.append({"id": identifier, "des_changes": values})

    for md, me in ((5, 5), (4, 5), (5, 4), (4, 6), (6, 4), (6, 6)):
        add(f"grid_{md}x{me}", MD=md, ME=me)
        add(f"stagger_{md}x{me}", MD=md, ME=me, staggered_matrix="CHECKED")
    for mdp, mep in (
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 3),
        (1, 3),
        (3, 1),
        (2, 4),
        (4, 2),
        (5, 5),
        (5, 2),
        (2, 5),
    ):
        add(f"depop_{mdp}_{mep}", depop_center="CHECKED", MDp=mdp, MEp=mep)
    for mdp, mep in ((2, 2), (3, 2), (2, 3), (3, 3)):
        add(f"even_depop_{mdp}_{mep}", MD=6, ME=5, depop_center="CHECKED", MDp=mdp, MEp=mep)
    add("stagger_depop", staggered_matrix="CHECKED", depop_center="CHECKED")
    all_cells = {(x, y) for x in range(5) for y in range(5)}
    perimeter = {(x, y) for x, y in all_cells if x in (0, 4) or y in (0, 4)}
    for name, cells, extra in (
        ("explicit24", all_cells - {(0, 0)}, {}),
        ("explicit24_stagger", all_cells - {(0, 0)}, {"staggered_matrix": "CHECKED"}),
        ("explicit24_depop", all_cells - {(0, 0)}, {"depop_center": "CHECKED"}),
        ("explicit_perimeter_center", perimeter, {"central_balls": "CHECKED", "MDc": 3, "MEc": 3}),
    ):
        add(name, balls=":".join(f"{x}x{y}" for x, y in sorted(cells)), **extra)
    for mdc, mec in ((1, 1), (2, 2), (3, 3), (2, 3), (3, 2), (4, 4)):
        add(f"center_{mdc}_{mec}", central_balls="CHECKED", MDc=mdc, MEc=mec)
    add(
        "center_stagger_3_3",
        central_balls="CHECKED",
        MDc=3,
        MEc=3,
        central_staggered_matrix="CHECKED",
    )
    add(
        "center_stagger_2_3",
        central_balls="CHECKED",
        MDc=2,
        MEc=3,
        central_staggered_matrix="CHECKED",
    )
    add("main_stagger_center", central_balls="CHECKED", MDc=3, MEc=3, staggered_matrix="CHECKED")
    add("depop_center_restore", depop_center="CHECKED", central_balls="CHECKED", MDc=3, MEc=3)
    add("pitch_0_65", e=0.65)
    add("diameter_0_4", b=0.4)
    add("height_0_5", A1=0.5)
    return items


def capture(installation, output):
    if output.exists():
        raise ValueError("capture target exists; use a new directory")
    output.mkdir(parents=True)
    baselines = []
    for family in FAMILIES:
        root = ET.parse(
            ROOT / f"flotherm_pack_data/templates/{family}/baseline/script.xml"
        ).getroot()
        baselines.append(
            {
                "id": family,
                "commands": [
                    ET.tostring(e, encoding="unicode") for e in root if e.tag == "new_package"
                ],
            }
        )
    result = replay(installation, baselines, output / "baselines")
    if result["errors"] or result["exit_code"] != 0 or len(result["exports"]) != 4:
        raise RuntimeError(f"baseline capture failed: {result}")
    for family in FAMILIES:
        directory = output / family
        inputs = directory / "inputs"
        inputs.mkdir(parents=True)
        baseline = read_des(output / "baselines" / f"{family}.des")
        cases = definitions()
        for case in cases:
            if family != "chip_array":
                # Set mode before loading: option setters reject some empty-array states.
                case["des_changes"]["radio_BGA_modeling"] = "3"
            path = inputs / f"{case['id']}.des"
            values = baseline | case["des_changes"]
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(path.name, "\n".join(f"{k}|{v}" for k, v in values.items()) + "\n")
            commands = [ET.tostring(ET.Element("load_des", filename=str(path)), encoding="unicode")]
            case["commands"] = commands
        (directory / "definitions.json").write_text(
            json.dumps(cases, indent=2) + "\n", encoding="utf-8"
        )
        result = replay(installation, cases, directory / "native")
        if result["errors"] or result["exit_code"] != 0 or len(result["exports"]) != len(cases):
            raise RuntimeError(f"capture failed: {family}: {result}")
        for case in cases:
            values = read_des(directory / "native" / f"{case['id']}.des")
            for key, value in case["des_changes"].items():
                if values.get(key) != value:
                    raise ValueError(f"input readback mismatch: {family}/{case['id']}/{key}")
        print(json.dumps({"family": family, "captured": len(cases)}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    capture(args.installation.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
