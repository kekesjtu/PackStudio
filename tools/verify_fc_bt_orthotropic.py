"""Compare native FC Core Via equivalence using physically identical BT material types."""

import argparse
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.floxml_validation.native import fingerprint
from tools.floxml_validation.native_suite import read_des
from tools.verify_via_matrix_sources import observe
from tools.verify_wb_via_stack_floxml import compare_tree, prepare_replay

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "flotherm_pack_data/validation/fc_bt_orthotropic_2026-10-26"
BASELINE = ROOT / "flotherm_pack_data/validation/via_matrix_sources_2026-10-25/baselines/fc.des"
CASES = {
    "builtin_bt": ("BT", None),
    "custom_constant": ("Audit BT Constant 20261026", "constant"),
    "custom_orthotropic": ("Audit BT Orthotropic 20261026", "orthotropic"),
}


def material_commands():
    result = []
    for name, kind in CASES.values():
        if kind is None:
            continue
        result.append('<create_material group_name="Substrate Dielectrics"/>')
        for prop, value in [
            ("name", name),
            ("conductivityType", kind),
            ("conductivity", 0.2),
            ("conductivityX", 0.2 if kind == "orthotropic" else 0.0),
            ("conductivityY", 0.2 if kind == "orthotropic" else 0.0),
            ("conductivityZ", 0.2 if kind == "orthotropic" else 0.0),
            ("density", 1900),
            ("specificHeat", 921),
            ("emissivity", 0.8),
        ]:
            element = ET.Element("modify_material", property_name=prop, new_value=str(value))
            ET.SubElement(element, "material_name", name="Material" if prop == "name" else name)
            result.append(ET.tostring(element, encoding="unicode"))
    return result


def prepare(installation, output, phase):
    inputs = output / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    members = []
    for index, (identifier, (name, _kind)) in enumerate(CASES.items()):
        path = inputs / f"{identifier}.des"
        if phase == "native":
            assert not path.exists()
            with zipfile.ZipFile(BASELINE) as source, zipfile.ZipFile(path, "w") as target:
                for member in source.namelist():
                    data = source.read(member)
                    if member.endswith(".des"):
                        text = data.decode()
                        original = "k_substr|Substrate PBGAFC (Typical)"
                        assert text.count(original) == 1
                        data = text.replace(original, f"k_substr|{name}").encode()
                    target.writestr(identifier + Path(member).suffix, data)
        else:
            path = output / "native" / f"{identifier}.des"
            assert path.exists()
        commands = material_commands() if index == 0 else []
        commands.append(ET.tostring(ET.Element("load_des", filename=str(path)), encoding="unicode"))
        members.append({"id": identifier, "commands": commands})
    directory = output / phase
    prepare_replay(installation, members, directory)
    (directory / "inputs.json").write_text(
        json.dumps(
            {"baseline_sha256": fingerprint(BASELINE), "materials": CASES},
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Prepared {phase}: {len(members)} cases")


def material_definitions(directory):
    """Check the selected substrate's actual exported conductivity representation."""
    definitions = {}
    for identifier, (name, kind) in CASES.items():
        tree = ET.parse(directory / f"{identifier}.xml")
        materials = [
            e for e in tree.iter() if e.tag.endswith("_material_att") and e.findtext("name") == name
        ]
        assert len(materials) == 1, (name, len(materials))
        expected = "biaxial_material_att" if kind == "orthotropic" else "isotropic_material_att"
        assert materials[0].tag == expected
        definitions[identifier] = {
            "tag": materials[0].tag,
            "fields": {child.tag: child.text for child in materials[0]},
        }
    return definitions


def verify(output):
    result = {"runs": {}, "exported_substrate_materials": {}, "cases": []}
    for phase in ("native", "reload"):
        directory = output / phase
        run = json.loads((directory / "run.json").read_text(encoding="utf-8-sig"))
        assert run["exit_code"] == 0 and not run["errors"]
        assert set(run["exports"]) == set(CASES)
        assert run["script_sha256"] == fingerprint(directory / "replay.xml")
        assert run["launcher_sha256"] == fingerprint(directory / "replay_wb_via_stack.ps1")
        for identifier in CASES:
            assert run["exports"][identifier] == fingerprint(directory / f"{identifier}.xml")
        result["runs"][phase] = run
        result["exported_substrate_materials"][phase] = material_definitions(directory)
    compare_tree(
        result["exported_substrate_materials"]["native"],
        result["exported_substrate_materials"]["reload"],
    )
    for identifier, (name, kind) in CASES.items():
        expected_des = read_des(BASELINE)
        expected_des["k_substr"] = name
        for phase in ("native", "reload"):
            assert read_des(output / phase / f"{identifier}.des") == expected_des
        first = observe(output / "native", identifier, "fc")
        second = observe(output / "reload", identifier, "fc")
        first["max_reload_difference"] = max(
            compare_tree(first[k], second[k]) for k in first.keys() - {"sha256"}
        )
        assert first["inherited_substrate"] == name
        compare_tree(first["selected_substrate_properties"], [0.2, 0.2, 0.2, 1900.0, 921.0])
        expected = [0.2] * 3 if kind == "orthotropic" else [0.0] * 3
        compare_tree(first["inferred_matrix"], expected + [1900.0, 921.0])
        first["conductivity_storage_type"] = kind or "builtin constant"
        first["reload_sha256"] = second["sha256"]
        result["cases"].append(first)
    result["summary"] = {
        "fresh_cases": len(CASES),
        "reload_cases": len(CASES),
        "orthotropic_bt_restores_matrix_conductivity": True,
        "custom_constant_reproduces_builtin_bt_anomaly": True,
        "all_passed": True,
    }
    (output / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    for case in result["cases"]:
        print(case["id"], case["equivalent_properties"], case["inferred_matrix"])


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
