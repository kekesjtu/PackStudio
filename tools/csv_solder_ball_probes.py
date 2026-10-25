"""Capture nonempty arbitrary-coordinate solder-ball maps using native DES/FloXML."""

import argparse
import csv
import io
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.floxml_validation.native import replay
from tools.floxml_validation.native_suite import read_des
from tools.solder_ball_array_probes import FAMILIES, ROOT

DEFAULT_OUTPUT = ROOT / "flotherm_pack_data/validation/csv_ball_map_2026-10-25/formal"
MAP_ROWS = [("A1", -1.1, 0.3), ("B2", 0.25, -0.7), ("C3", 1.4, 0.8)]


def map_payload(rows):
    return "\n".join(f"{name},{x:.6f},{y:.6f}" for name, x, y in rows)


def saved_map(path):
    with zipfile.ZipFile(path) as archive:
        member = next(name for name in archive.namelist() if name.endswith(".var2"))
        text = archive.read(member).decode("utf-8")
    return [(name, float(x), float(y)) for name, x, y in csv.reader(io.StringIO(text)) if name]


def definitions():
    cases = []

    def add(identifier, rows=MAP_ROWS, **changes):
        values = {
            "MD": "5",
            "ME": "5",
            "e": "0.8",
            "b": "0.5",
            "A1": "0.4",
            "csvBGA": "CHECKED",
            "balls": "",
            "depop_center": "UNCHECKED",
            "MDp": "2",
            "MEp": "2",
            "staggered_matrix": "UNCHECKED",
            "central_balls": "UNCHECKED",
            "MDc": "2",
            "MEc": "2",
            "central_staggered_matrix": "UNCHECKED",
        }
        values.update({k: str(v) for k, v in changes.items()})
        cases.append({"id": identifier, "map_rows": rows, "des_changes": values})

    add("csv3")
    add("csv3_grid_counts", MD=3, ME=7)
    add("csv3_pitch", e=1.1)
    add("csv3_diameter", b=0.4)
    add("csv3_height", A1=0.5)
    add("csv3_stagger", staggered_matrix="CHECKED")
    add("csv3_depop", depop_center="CHECKED")
    add("csv3_explicit", balls="0x0")
    add("csv3_center", central_balls="CHECKED")
    add("csv3_center_stagger", central_balls="CHECKED", central_staggered_matrix="CHECKED")
    add(
        "csv3_all_filters",
        balls="0x0",
        depop_center="CHECKED",
        staggered_matrix="CHECKED",
        central_balls="CHECKED",
        central_staggered_matrix="CHECKED",
    )
    add("csv1_offset", rows=[("P1", 0.7, -0.2)])
    add("csv3_reordered", rows=list(reversed(MAP_ROWS)))
    add("csv3_translated", rows=[(n, x + 0.35, y - 0.4) for n, x, y in MAP_ROWS])
    add("csv2_same_position", rows=[("D1", 0.25, -0.7), ("D2", 0.25, -0.7)])
    add("csv_empty", rows=[])
    add("csv_disabled", csvBGA="UNCHECKED")
    add("csv_disabled_explicit", csvBGA="UNCHECKED", balls="0x0")
    return cases


def write_input(path, baseline, values, rows):
    with (
        zipfile.ZipFile(baseline) as source,
        zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as target,
    ):
        target.writestr(path.name, "\n".join(f"{k}|{v}" for k, v in values.items()) + "\n")
        for name in source.namelist():
            if ".var" in name:
                suffix = name[name.rindex(".var") :]
                payload = (
                    map_payload(rows).encode("utf-8") if suffix == ".var2" else source.read(name)
                )
                target.writestr(path.stem + suffix, payload)


def capture(installation, output):
    if output.exists():
        raise ValueError("capture directory already exists; use a new directory")
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
    if result["exit_code"] != 0 or result["errors"] or len(result["exports"]) != 4:
        raise RuntimeError(f"baseline capture failed: {result}")
    csv_path = output / "nonempty-map.csv"
    csv_path.write_text("ID,X,Y\n" + map_payload(MAP_ROWS) + "\n", encoding="utf-8")
    for family in FAMILIES:
        directory = output / family
        inputs = directory / "inputs"
        inputs.mkdir(parents=True)
        baseline_path = output / "baselines" / f"{family}.des"
        baseline = read_des(baseline_path)
        cases = definitions()
        for case in cases:
            if family != "chip_array":
                case["des_changes"]["radio_BGA_modeling"] = "3"
            path = inputs / f"{case['id']}.des"
            write_input(path, baseline_path, baseline | case["des_changes"], case["map_rows"])
            case["commands"] = [
                ET.tostring(ET.Element("load_des", filename=str(path)), encoding="unicode")
            ]
        (directory / "definitions.json").write_text(
            json.dumps(cases, indent=2) + "\n", encoding="utf-8"
        )
        result = replay(installation, cases, directory / "native")
        if result["exit_code"] != 0 or result["errors"] or len(result["exports"]) != len(cases):
            raise RuntimeError(f"capture failed: {family}: {result}")
        for case in cases:
            saved = directory / "native" / f"{case['id']}.des"
            values = read_des(saved)
            assert all(values.get(k) == v for k, v in case["des_changes"].items())
            expected = [(n, round(x, 6), round(y, 6)) for n, x, y in case["map_rows"]]
            assert saved_map(saved) == expected, f"map payload changed: {family}/{case['id']}"
        print(json.dumps({"family": family, "captured": len(cases)}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    capture(args.installation.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
