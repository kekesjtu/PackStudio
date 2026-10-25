"""Identify native Via-equivalent matrix sources with controlled material changes."""

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
DEFAULT_OUTPUT = ROOT / "flotherm_pack_data/validation/via_matrix_sources_2026-10-25"
PROFILES = {
    "wb": (
        "pbga_wb",
        "opt_v2_c007_modelthermalviasas_orthotropiccuboid",
        "thermal_via",
        0.25,
        0.025,
        1.27,
    ),
    "fc": (
        "pbga_fc",
        "opt_v2_c007_modelcoreviasas_orthotropiccuboid",
        "core_vias",
        0.2,
        0.025,
        0.8,
    ),
    "qfn": ("qfn", "opt_v2_c003_modelviasas_lumped", "vias", 0.2, 0.02, 0.5),
}
VARIANTS = [
    ("wb_fr4", "wb", "k_substr", "FR4"),
    ("fc_bt", "fc", "k_substr", "BT"),
    ("fc_fr4_fibre", "fc", "k_substr", "FR4 (25% Fibre)"),
    ("qfn_encap", "qfn", "k_encap", "Epoxy Overmold (Typical)"),
    ("qfn_attach", "qfn", "k_da", "QMI 595"),
]


def load_command(path):
    return ET.tostring(ET.Element("load_des", filename=str(path)), encoding="unicode")


def prepare(installation, output, phase):
    members = []
    if phase == "baselines":
        if output.exists():
            raise ValueError("choose a new output directory")
        output.mkdir(parents=True)
        sources = {}
        for identifier, (family, option, *_rest) in PROFILES.items():
            path = ROOT / "flotherm_pack_data/templates" / family / "xml_variations/option_switches"
            path = path / option / "script.xml"
            commands = [
                ET.tostring(e, encoding="unicode")
                for e in ET.parse(path).getroot()
                if e.tag in {"new_package", "modify_component"}
            ]
            members.append({"id": identifier, "commands": commands})
            sources[identifier] = {"path": str(path), "sha256": fingerprint(path)}
        (output / "sources.json").write_text(json.dumps(sources, indent=2), encoding="utf-8")
    elif phase in {"variants", "anisotropic"}:
        inputs = output / "inputs"
        inputs.mkdir(exist_ok=True)
        for identifier, profile, key, material in VARIANTS:
            if (identifier == "fc_fr4_fibre") != (phase == "anisotropic"):
                continue
            values = read_des(output / "baselines" / f"{profile}.des")
            values[key] = material
            path = inputs / f"{identifier}.des"
            assert not path.exists()
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(path.name, "\n".join(f"{k}|{v}" for k, v in values.items()) + "\n")
            members.append({"id": identifier, "commands": [load_command(path)]})
    else:
        for identifier in PROFILES:
            path = output / "baselines" / f"{identifier}.des"
            read_des(path)
            members.append({"id": identifier, "commands": [load_command(path)]})
        for identifier, *_rest in VARIANTS:
            source_phase = "anisotropic" if identifier == "fc_fr4_fibre" else "variants"
            path = output / source_phase / f"{identifier}.des"
            read_des(path)
            members.append({"id": identifier, "commands": [load_command(path)]})
    prepare_replay(installation, members, output / phase)
    print(f"Prepared {phase}: {len(members)} cases")


def observe(directory, identifier, profile):
    path = directory / f"{identifier}.xml"
    values = read_des(path.with_suffix(".des"))
    document = read(path)
    _family, _option, name, diameter, plating, pitch = PROFILES[profile]
    box = next(block for block in document.boxes if block.name == name)
    length = 4 * pitch + diameter
    near(box.size[0], length)
    near(box.size[1], length)
    fraction = 25 * math.pi * diameter**2 / (4 * length**2)
    shell = 1 - ((diameter - 2 * plating) / diameter) ** 2
    metal = [385, 385, 385, 8930, 385]
    via = [shell * k for k in metal[:4]] + [metal[4]]
    equivalent = list(document.materials[box.material])
    density = (equivalent[3] - fraction * via[3]) / (1 - fraction)
    heat = equivalent[3] * equivalent[4] - fraction * via[3] * via[4]
    heat /= (1 - fraction) * density
    kz = (equivalent[2] - fraction * via[2]) / (1 - fraction)
    inferred = [equivalent[0], equivalent[1], kz, density, heat]
    inherited = values.get("k_substr") if profile in {"wb", "fc"} else None
    return {
        "id": identifier,
        "profile": profile,
        "selected_materials": {k: v for k, v in values.items() if k.startswith("k_") and v},
        "has_k_substr": "k_substr" in values,
        "inherited_substrate": inherited,
        "inferred_matrix": inferred,
        "selected_substrate_properties": list(document.materials[inherited]) if inherited else None,
        "equivalent_properties": equivalent,
        "via_fraction": fraction,
        "single_via_properties": via,
        "origin_mm": list(box.origin),
        "size_mm": list(box.size),
        "sha256": {"floxml": fingerprint(path), "des": fingerprint(path.with_suffix(".des"))},
    }


def library_candidates():
    records, matching = [], []
    for path in sorted((ROOT / "default_parameters/materials").glob("*/*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        conductivity = record["conductivity"]
        tensor = (
            [conductivity["value"]] * 3
            if conductivity["model"] == "constant_isotropic"
            else [conductivity.get(axis) for axis in "xyz"]
        )
        if None in tensor:
            native = record["native_storage"]
            tensor = [native["conductivity_w_m_k"]] * 3
        properties = tensor + [record["density"]["value"], record["specific_heat"]["value"]]
        item = {
            "name": record["name"],
            "category": record["category"],
            "properties": properties,
            "source": str(path.relative_to(ROOT)),
            "sha256": fingerprint(path),
        }
        records.append(item)
        if properties[3:] == [1200, 880]:
            matching.append(item)
    exact = [item for item in records if item["properties"] == [0.32, 0.32, 0.32, 1200, 880]]
    return {
        "library_entries_checked": len(records),
        "exact_qfn_matches": exact,
        "same_density_and_heat": matching,
    }


def verify(output):
    result = {"runs": {}, "cases": [], "library": library_candidates()}
    phases = {
        "baselines": list(PROFILES),
        "variants": [item[0] for item in VARIANTS if item[0] != "fc_fr4_fibre"],
        "anisotropic": ["fc_fr4_fibre"],
        "reload-confirmed": list(PROFILES) + [item[0] for item in VARIANTS],
    }
    for phase, identifiers in phases.items():
        directory = output / phase
        run = json.loads((directory / "run.json").read_text(encoding="utf-8-sig"))
        assert run["exit_code"] == 0 and not run["errors"]
        assert set(run["exports"]) == set(identifiers)
        assert run["script_sha256"] == fingerprint(directory / "replay.xml")
        assert run["launcher_sha256"] == fingerprint(directory / "replay_wb_via_stack.ps1")
        for identifier in identifiers:
            assert run["exports"][identifier] == fingerprint(directory / f"{identifier}.xml")
        result["runs"][phase] = run
    definitions = [(name, name, None, None) for name in PROFILES] + VARIANTS
    for identifier, profile, key, material in definitions:
        phase = (
            "anisotropic" if identifier == "fc_fr4_fibre" else ("variants" if key else "baselines")
        )
        first = observe(output / phase, identifier, profile)
        second = observe(output / "reload-confirmed", identifier, profile)
        error = max(compare_tree(first[k], second[k]) for k in first.keys() - {"sha256"})
        if key:
            assert first["selected_materials"][key] == material
        if first["inherited_substrate"]:
            if identifier == "fc_bt":
                compare_tree(first["inferred_matrix"], [0.0, 0.0, 0.0, 1900.0, 921.0])
            else:
                compare_tree(first["inferred_matrix"], first["selected_substrate_properties"])
        if profile == "qfn":
            compare_tree(first["inferred_matrix"], [0.32, 0.32, 0.32, 1200.0, 880.0])
            assert not first["has_k_substr"]
        first["max_reload_difference"] = error
        first["reload_sha256"] = second["sha256"]
        result["cases"].append(first)
    for case in result["cases"]:
        print(case["id"], case["inherited_substrate"], case["inferred_matrix"])
    result["summary"] = {
        "fresh_cases": len(definitions),
        "reload_cases": len(definitions),
        "wb_and_fc_anisotropic_substrate_inheritance_verified": True,
        "fc_isotropic_substrate_probe_anomaly": True,
        "qfn_independent_of_tested_encap_and_attach": True,
        "qfn_exact_builtin_match": bool(result["library"]["exact_qfn_matches"]),
        "all_passed": True,
    }
    (output / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--installation", type=Path)
    parser.add_argument(
        "--prepare", choices=("baselines", "variants", "anisotropic", "reload-confirmed")
    )
    args = parser.parse_args()
    if args.prepare:
        if not args.installation:
            parser.error("--prepare requires --installation")
        prepare(args.installation.resolve(), args.output.resolve(), args.prepare)
    else:
        verify(args.output.resolve())


if __name__ == "__main__":
    main()
