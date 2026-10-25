"""Capture and check native WB via heights with unequal outer copper thicknesses."""

import argparse
import json
import math
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.floxml_validation.native import fingerprint
from tools.floxml_validation.native_suite import read_des
from tools.floxml_validation.reader import read

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "flotherm_pack_data/validation/wb_via_stack_2026-10-25-complete"


def definitions():
    cases = []
    for layers, top, bottom, a1, a2 in [
        (4, 0.018, 0.018, 0.6, 0.56),
        (4, 0.01, 0.018, 0.6, 0.56),
        (4, 0.018, 0.04, 0.6, 0.56),
        (4, 0.01, 0.04, 0.6, 0.56),
        (4, 0.04, 0.01, 0.6, 0.56),
        (4, 0.025, 0.025, 0.6, 0.56),
        (4, 0.012, 0.03, 0.8, 0.7),
        (2, 0.01, 0.04, 0.6, 0.36),
        (2, 0.04, 0.01, 0.6, 0.36),
    ]:
        identifier = f"layers{layers}_top{top:g}_bottom{bottom:g}_a1{a1:g}_a2{a2:g}"
        cases.append(
            {
                "id": identifier.replace(".", "_"),
                "layers": layers,
                "top": top,
                "bottom": bottom,
                "a1": a1,
                "a2": a2,
            }
        )
    return cases


def commands(case):
    package = ET.Element("new_package", package_type="pbga_wb")
    for name, value in {
        "designName": case["id"],
        "outlineType": "standardOutline",
        "jedecFootprint": "PBGA_121_15X15mm",
        "dieType": "actualDie",
        "substrateLayer": f"{case['layers']}-Layer",
        "topSignalLayerThickness": case["top"],
        "bottomSignalLayerThickness": case["bottom"],
        "includeSlug": "false",
    }.items():
        ET.SubElement(package, "new_value", property_name=name, new_value=str(value))
    result = [ET.tostring(package, encoding="unicode")]
    for component, prop, value in [
        ("packageSubstrate", "substrateThicknessA2", case["a2"]),
        ("solderBalls", "substrateStandoffA1", case["a1"]),
    ]:
        element = ET.Element(
            "modify_component", name=component, property_name=prop, new_value=str(value)
        )
        result.append(ET.tostring(element, encoding="unicode"))
    return result


def prepare_replay(installation, cases, directory):
    directory.mkdir(parents=True)
    config = directory / "config"
    config.mkdir()
    for path in (installation / "config").iterdir():
        if path.is_file():
            shutil.copy2(path, config / path.name)
    shutil.copytree(
        installation / "flocentral/flopack",
        directory / "central/flopack",
        ignore=shutil.ignore_patterns("Library"),
    )
    (directory / "central/flopack/Library").mkdir()
    (directory / "user").mkdir()
    script = ET.Element("flopack_xml_log_file", version="1.0")
    for case in cases:
        script.extend(ET.fromstring(command) for command in case["commands"])
        ET.SubElement(script, "save_des", filename=str(directory / f"{case['id']}.des"))
        ET.SubElement(script, "export_floxml", filename=str(directory / f"{case['id']}.xml"))
    ET.SubElement(script, "quit")
    ET.ElementTree(script).write(directory / "replay.xml", encoding="utf-8", xml_declaration=True)
    launcher = ROOT / "tools/replay_wb_via_stack.ps1"
    shutil.copy2(launcher, directory / launcher.name)


def prepare_native(installation, output):
    if output.exists():
        raise ValueError("capture target exists; choose a new output directory")
    output.mkdir(parents=True)
    cases = definitions()
    (output / "definitions.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")
    first = [{"id": c["id"], "commands": commands(c)} for c in cases]
    prepare_replay(installation, first, output / "native")


def prepare_reload(installation, output):
    cases = json.loads((output / "definitions.json").read_text(encoding="utf-8"))
    run = json.loads((output / "native/run.json").read_text(encoding="utf-8-sig"))
    assert run["exit_code"] == 0 and not run["errors"]
    assert set(run["exports"]) == {c["id"] for c in cases}
    for case in cases:
        observe(output / "native", case)
    second = [
        {
            "id": c["id"],
            "commands": [
                ET.tostring(
                    ET.Element("load_des", filename=str(output / "native" / f"{c['id']}.des")),
                    encoding="unicode",
                )
            ],
        }
        for c in cases
    ]
    prepare_replay(installation, second, output / "reload")


def near(actual, expected):
    if not math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-11):
        raise AssertionError((actual, expected))


def compare_tree(actual, expected):
    if isinstance(actual, float):
        near(actual, expected)
        return abs(actual - expected)
    if isinstance(actual, dict):
        assert actual.keys() == expected.keys()
        return max((compare_tree(actual[k], expected[k]) for k in actual), default=0.0)
    if isinstance(actual, list):
        assert len(actual) == len(expected)
        return max((compare_tree(a, b) for a, b in zip(actual, expected, strict=True)), default=0.0)
    assert actual == expected
    return 0.0


def observe(directory, case):
    path = directory / f"{case['id']}.xml"
    saved = path.with_suffix(".des")
    values = read_des(saved)
    for key, expected in {
        "tz1": case["top"],
        "tz6": case["bottom"],
        "A1": case["a1"],
        "A2": case["a2"],
    }.items():
        near(float(values[key]), expected)
    assert values["radio_Via_modeling"] == "3"
    document = read(path)
    vias = [b for b in document.boxes if b.name.startswith("thermal_via_")]
    flag = next(b for b in document.boxes if b.name == "die_flag")
    bottom = next(b for b in document.boxes if b.name == "bottom_trace")
    substrate = next(b for b in document.boxes if b.name == "dielectric")
    internals = [b for b in document.boxes if b.name in {"trace_1", "trace_2"}]
    assert len(internals) == (2 if case["layers"] == 4 else 0)
    assert len(vias) == int(values["NVx"]) * int(values["NVy"])
    near(flag.size[2], case["top"])
    near(bottom.size[2], case["bottom"])
    near(flag.origin[2], case["a1"] + case["a2"] - case["top"])
    near(bottom.origin[2], case["a1"])
    near(substrate.origin[2], case["a1"])
    near(substrate.size[2], case["a2"])
    via = vias[0]
    for block in vias:
        near(block.origin[2], via.origin[2])
        near(block.size[2], via.size[2])
        near(block.size[0], math.sqrt(math.pi) * float(values["dv"]) / 2)
        near(block.size[1], block.size[0])
    a1, a2, top, lower = (case[k] for k in ("a1", "a2", "top", "bottom"))
    candidates = {
        "top_offset": a1 + top,
        "bottom_offset": a1 + lower,
    }
    residuals = {k: via.origin[2] - expected for k, expected in candidates.items()}
    observed = {
        "id": case["id"],
        "inputs_mm": {"A1": a1, "A2": a2, "top": top, "bottom": lower},
        "layers": case["layers"],
        "input_readback": {k: values[k] for k in ("A1", "A2", "tz1", "tz6", "NVx", "NVy")},
        "via_count": len(vias),
        "via_zmin_mm": via.origin[2],
        "via_height_mm": via.size[2],
        "via_zmax_mm": via.high[2],
        "bottom_trace_range_mm": [bottom.origin[2], bottom.high[2]],
        "flag_range_mm": [flag.origin[2], flag.high[2]],
        "bottom_clearance_mm": via.origin[2] - bottom.high[2],
        "top_clearance_mm": flag.origin[2] - via.high[2],
        "start_hypothesis_residuals_mm": residuals,
        "height_residual_mm": via.size[2] - (a2 - top - lower),
        "internal_layers": [
            {"name": b.name, "zmin_mm": b.origin[2], "height_mm": b.size[2]} for b in internals
        ],
        "disconnect_regions": [
            {"name": b.name, "zmin_mm": b.origin[2], "height_mm": b.size[2]}
            for b in document.boxes
            if b.name.startswith("discon")
        ],
        "via_material": list(document.materials[via.material]),
        "sha256": {"floxml": fingerprint(path), "des": fingerprint(saved)},
    }
    return observed


def verify(output):
    cases = json.loads((output / "definitions.json").read_text(encoding="utf-8"))
    result = {"cases": [], "runs": {}}
    for phase in ("native", "reload"):
        directory = output / phase
        run = json.loads((directory / "run.json").read_text(encoding="utf-8-sig"))
        assert run["exit_code"] == 0 and not run["errors"]
        assert set(run["exports"]) == {c["id"] for c in cases}
        assert run["script_sha256"] == fingerprint(directory / "replay.xml")
        launcher = directory / "replay_wb_via_stack.ps1"
        assert run["launcher_sha256"] == fingerprint(launcher)
        for case in cases:
            assert run["exports"][case["id"]] == fingerprint(directory / f"{case['id']}.xml")
        result["runs"][phase] = run
    for case in cases:
        observed = observe(output / "native", case)
        reloaded = observe(output / "reload", case)
        difference = max(
            compare_tree(observed[key], reloaded[key]) for key in observed.keys() - {"sha256"}
        )
        observed["max_reload_numeric_difference"] = difference
        observed["reload_sha256"] = reloaded["sha256"]
        result["cases"].append(observed)
    (output / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    for case in result["cases"]:
        near(case["start_hypothesis_residuals_mm"]["top_offset"], 0)
        near(case["height_residual_mm"], 0)
    result["conclusion"] = {
        "z_min": "A1 + t_top",
        "height": "A2 - t_top - t_bottom",
        "z_max": "A1 + A2 - t_bottom",
        "offset_from_between_copper_planes": "t_top - t_bottom",
        "fresh_cases": len(cases),
        "reloaded_cases": len(cases),
        "passed": True,
    }
    (output / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["conclusion"], indent=2))
    for case in result["cases"]:
        print(
            f"{case['id']}: count={case['via_count']} "
            f"z={case['via_zmin_mm']:.6f}..{case['via_zmax_mm']:.6f} "
            f"h={case['via_height_mm']:.6f} "
            f"gaps={case['bottom_clearance_mm']:.6f}/{case['top_clearance_mm']:.6f}"
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installation", type=Path)
    parser.add_argument("--prepare", choices=("native", "reload"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    if args.prepare:
        if not args.installation:
            parser.error("--prepare requires --installation")
        function = prepare_native if args.prepare == "native" else prepare_reload
        function(args.installation.resolve(), output)
        print(f"Prepared {output / args.prepare / 'replay.xml'}")
    else:
        verify(output)


if __name__ == "__main__":
    main()
