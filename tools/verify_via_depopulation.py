"""Measure native Via depopulation geometry and equivalent properties, then reload."""

import argparse
import json
import math
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.floxml_validation.native import fingerprint
from tools.floxml_validation.native_suite import read_des
from tools.floxml_validation.reader import read
from tools.verify_wb_via_stack_floxml import compare_tree, near, prepare_replay

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "flotherm_pack_data/validation/via_depopulation_2026-10-25-confirmed"
BASELINES = ROOT / "flotherm_pack_data/validation/via_matrix_sources_2026-10-25/baselines"
PROFILES = {
    "wb_ortho": ("wb", "thermalVias", "modelThermalViasAs", "orthotropicCuboid", "4"),
    "wb_iso": ("wb", "thermalVias", "modelThermalViasAs", "isotropicCuboid", "2"),
    "wb_discrete": ("wb", "thermalVias", "modelThermalViasAs", "discreteCuboids", "3"),
    "fc_ortho": ("fc", "coreVias", "modelCoreViasAs", "orthotropicCuboid", "4"),
    "fc_discrete": ("fc", "coreVias", "modelCoreViasAs", "discreteCuboids", "3"),
}


def definitions():
    full = {(x, y) for x in range(5) for y in range(5)}
    masks = {
        "empty_list": set(),
        "full25": full,
        "corner24": full - {(0, 0)},
        "perimeter16": {(x, y) for x, y in full if x in (0, 4) or y in (0, 4)},
        "block16": {(x, y) for x in range(4) for y in range(4)},
        "corners4": {(0, 0), (0, 4), (4, 0), (4, 4)},
        "cluster4": {(0, 0), (0, 1), (1, 0), (1, 1)},
        "single1": {(0, 0)},
    }
    return [
        {"id": f"{profile}_{name}", "profile": profile, "mask": sorted(map(list, cells))}
        for profile in PROFILES
        for name, cells in masks.items()
    ]


def command(tag, **attributes):
    return ET.tostring(ET.Element(tag, **attributes), encoding="unicode")


def prepare(installation, output, phase):
    cases = definitions()
    members = []
    for case in cases:
        family, component, prop, mode, _code = PROFILES[case["profile"]]
        if phase == "native":
            cells = ":".join(f"{x}x{y}" for x, y in case["mask"])
            commands = [
                command("load_des", filename=str(BASELINES / f"{family}.des")),
                command(
                    "modify_component", name="modelingOptions", property_name=prop, new_value=mode
                ),
            ]
            if cells:
                commands.append(
                    command(
                        "modify_component",
                        name=component,
                        property_name="depopulationDialog",
                        new_value=cells,
                    )
                )
        else:
            commands = [command("load_des", filename=str(output / "native" / f"{case['id']}.des"))]
        members.append({"id": case["id"], "commands": commands})
    prepare_replay(installation, members, output / phase)
    print(f"Prepared {phase}: {len(cases)} cases")


def observe(directory, case):
    profile = case["profile"]
    family, _component, _prop, _mode, mode_code = PROFILES[profile]
    path = directory / f"{case['id']}.xml"
    values = read_des(path.with_suffix(".des"))
    assert values["radio_Via_modeling"] == mode_code
    assert values["NVx"] == values["NVy"] == "5"
    expected_mask = ":".join(f"{x}x{y}" for x, y in case["mask"])
    with zipfile.ZipFile(path.with_suffix(".des")) as archive:
        stored = archive.read(f"{case['id']}.var3").decode()
    assert stored == expected_mask
    document = read(path)
    prefix = "thermal_via" if family == "wb" else "core_via"
    blocks = [b for b in document.boxes if b.name.startswith(prefix)]
    count = len(case["mask"]) or 25
    diameter, plating, pitch = (float(values[k]) for k in ("dv", "tpl", "ev"))
    shell = 1 - ((diameter - 2 * plating) / diameter) ** 2
    single = [shell * 385] * 3 + [shell * 8930, 385]
    length = 4 * pitch + diameter
    fraction = count * math.pi * diameter**2 / (4 * length**2)
    if profile.endswith("discrete"):
        assert len(blocks) == count
        side = math.sqrt(math.pi) * diameter / 2
        actual_cells = set()
        for box in blocks:
            near(box.size[0], side)
            near(box.size[1], side)
            compare_tree(list(document.materials[box.material]), single)
            xy = [(box.origin[i] + side / 2) / pitch + 2 for i in (0, 1)]
            actual_cells.add(tuple(round(c) for c in xy))
        expected = {(x, 4 - y) for x, y in case["mask"]} or {
            (x, y) for x in range(5) for y in range(5)
        }
        assert actual_cells == expected
    else:
        assert len(blocks) == 1
        box = blocks[0]
        for i in (0, 1):
            near(box.size[i], length)
            near(box.origin[i], -length / 2)
        matrix = [0.2, 0.2, 0.2, 1900, 921] if family == "wb" else [20, 20, 4, 1900, 921]
        density = fraction * single[3] + (1 - fraction) * matrix[3]
        heat = fraction * single[3] * single[4] + (1 - fraction) * matrix[3] * matrix[4]
        kz = fraction * single[2] + (1 - fraction) * matrix[2]
        kxy = kz if profile == "wb_iso" else matrix[0]
        compare_tree(
            list(document.materials[box.material]), [kxy, kxy, kz, density, heat / density]
        )
    return {
        **case,
        "retained_count": count,
        "fraction": fraction,
        "blocks": [
            {
                "name": b.name,
                "origin": list(b.origin),
                "size": list(b.size),
                "properties": list(document.materials[b.material]),
            }
            for b in blocks
        ],
    }


def verify(output):
    result = {"runs": {}, "cases": []}
    cases = definitions()
    for phase in ("native", "reload"):
        directory = output / phase
        run = json.loads((directory / "run.json").read_text(encoding="utf-8-sig"))
        assert run["exit_code"] == 0 and not run["errors"]
        assert set(run["exports"]) == {c["id"] for c in cases}
        assert run["script_sha256"] == fingerprint(directory / "replay.xml")
        assert run["launcher_sha256"] == fingerprint(directory / "replay_wb_via_stack.ps1")
        for case in cases:
            assert run["exports"][case["id"]] == fingerprint(directory / f"{case['id']}.xml")
        result["runs"][phase] = run
    for case in cases:
        first = observe(output / "native", case)
        second = observe(output / "reload", case)
        error = compare_tree(first, second)
        if not case["profile"].endswith("discrete"):
            reference = read(output / "native" / f"{case['profile']}_empty_list.xml")
            name = first["blocks"][0]["name"]
            baseline = next(b for b in reference.boxes if b.name == name)
            compare_tree(first["blocks"][0]["origin"], list(baseline.origin))
            compare_tree(first["blocks"][0]["size"], list(baseline.size))
        first["max_reload_difference"] = error
        first["sha256"] = {
            phase: fingerprint(output / phase / f"{case['id']}.xml")
            for phase in ("native", "reload")
        }
        result["cases"].append(first)
    result["summary"] = {
        "fresh_cases": len(cases),
        "reload_cases": len(cases),
        "all_passed": True,
        "fixed_nominal_envelope": True,
        "fraction_uses_retained_count": True,
        "empty_list_means_full_array": True,
    }
    (output / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--installation", type=Path)
    parser.add_argument("--prepare", choices=("native", "reload"))
    args = parser.parse_args()
    if args.prepare:
        if not args.installation:
            parser.error("--prepare requires --installation")
        prepare(args.installation.resolve(), args.output.resolve(), args.prepare)
    else:
        verify(args.output.resolve())


if __name__ == "__main__":
    main()
