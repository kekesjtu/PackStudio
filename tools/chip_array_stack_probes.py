"""Prepare native Chip Array via-stack and metal-table experiments."""

import argparse
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.floxml_validation.native_suite import read_des
from tools.verify_wb_via_stack_floxml import prepare_replay

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "flotherm_pack_data/validation/chip_array_stack_2026-10-25"


def definitions():
    cases = []
    for layers in (2, 4):
        thickness = 0.36 if layers == 2 else 0.56
        for top, bottom, a1, a2, mode, filled in [
            (0.018, 0.018, 0.4, thickness, "accurate", False),
            (0.01, 0.018, 0.4, thickness, "accurate", False),
            (0.018, 0.04, 0.4, thickness, "accurate", False),
            (0.01, 0.04, 0.4, thickness, "accurate", False),
            (0.04, 0.01, 0.4, thickness, "accurate", False),
            (0.025, 0.025, 0.4, thickness, "accurate", False),
            (0.012, 0.03, 0.6, 0.7, "accurate", False),
            (0.01, 0.04, 0.4, thickness, "approximate", False),
            (0.04, 0.01, 0.4, thickness, "approximate", False),
            (0.01, 0.04, 0.4, thickness, "accurate", True),
        ]:
            identifier = (
                f"l{layers}_t{top:g}_b{bottom:g}_a1{a1:g}_a2{a2:g}_"
                f"{mode}_{'filled' if filled else 'hollow'}"
            ).replace(".", "_")
            cases.append(
                dict(
                    id=identifier,
                    layers=layers,
                    top=top,
                    bottom=bottom,
                    a1=a1,
                    a2=a2,
                    mode=mode,
                    filled=filled,
                )
            )
    return cases


def command(component, prop, value):
    return ET.tostring(
        ET.Element("modify_component", name=component, property_name=prop, new_value=str(value)),
        encoding="unicode",
    )


def commands(case):
    package = ET.Element("new_package", package_type="chip_array")
    for name, value in {
        "designName": case["id"],
        "outlineType": "standardOutline",
        "jedecFootprint": "ChipArray_24_4X4mm_0_8",
        "dieType": "actualDie",
        "substrateLayer": f"{case['layers']}-Layer",
        "topSignalLayerThickness": case["top"],
        "bottomSignalLayerThickness": case["bottom"],
    }.items():
        ET.SubElement(package, "new_value", property_name=name, new_value=str(value))
    result = [
        ET.tostring(package, encoding="unicode"),
        command("overallPackage", "substrateThicknessA2", case["a2"]),
        command("solderBalls", "substrateStandoffA1", case["a1"]),
    ]
    if case["mode"] == "approximate":
        result.append(command("modelingOptions", "viaModeling", "approximate"))
    if case["filled"]:
        result.append(command("vias", "filledVias", "yes"))
    return result


def prepare_native(installation, output):
    if output.exists():
        raise ValueError("use a new output directory")
    output.mkdir(parents=True)
    cases = definitions()
    (output / "definitions.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")
    prepare_replay(
        installation, [{"id": c["id"], "commands": commands(c)} for c in cases], output / "native"
    )


def prepare_reload(installation, output):
    cases = json.loads((output / "definitions.json").read_text(encoding="utf-8"))
    if (output / "metal-definitions.json").exists():
        cases += json.loads((output / "metal-definitions.json").read_text(encoding="utf-8"))
    members = []
    for case in cases:
        phase = "metals" if "des_changes" in case else "native"
        source = output / phase / f"{case['id']}.des"
        read_des(source)
        members.append(
            {
                "id": case["id"],
                "commands": [
                    ET.tostring(ET.Element("load_des", filename=str(source)), encoding="unicode")
                ],
            }
        )
    prepare_replay(installation, members, output / "reload")


def prepare_metals(installation, output):
    baselines = {}
    for case in definitions():
        if case["top"] == case["bottom"] == 0.018:
            baselines[case["layers"]] = case
    cases = []
    for layers, name, changes in [
        (2, "coverage_top50", {"coveragea1": "50"}),
        (4, "coverage_top50_inner35", {"coverage1": "50", "coverage2": "35"}),
        (4, "depths", {"z2": "0.12", "z3": "0.33"}),
        (4, "inner_thickness", {"tz2": "0.025", "tz3": "0.05"}),
        (2, "top_hole", {}),
        (4, "top_hole", {}),
        (2, "offset", {"vxoff": "0.2", "vyoff": "0.1"}),
        (4, "grid", {"MD": "4", "ME": "6", "e": "0.7"}),
    ]:
        case = baselines[layers] | {
            "id": f"l{layers}_{name}",
            "des_changes": changes,
        }
        cases.append(case)
    inputs = output / "metal-inputs"
    inputs.mkdir()
    members = []
    for case in cases:
        baseline = baselines[case["layers"]]
        values = read_des(output / "native" / f"{baseline['id']}.des") | case["des_changes"]
        path = inputs / f"{case['id']}.des"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(path.name, "\n".join(f"{k}|{v}" for k, v in values.items()) + "\n")
        commands = [ET.tostring(ET.Element("load_des", filename=str(path)), encoding="unicode")]
        if case["id"].endswith("top_hole"):
            commands += [
                command("metalLayers", "lengthLml", 1.4),
                command("metalLayers", "widthWml", 1.0),
            ]
        members.append({"id": case["id"], "commands": commands})
    (output / "metal-definitions.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")
    prepare_replay(installation, members, output / "metals")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--prepare", choices=("native", "metals", "reload"), required=True)
    args = parser.parse_args()
    {"native": prepare_native, "metals": prepare_metals, "reload": prepare_reload}[args.prepare](
        args.installation.resolve(), args.output.resolve()
    )
    print(f"Prepared {args.prepare}")


if __name__ == "__main__":
    main()
