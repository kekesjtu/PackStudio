"""Validate equivalent geometry and k/rho/cp using exported FloXML and material JSONs."""

import argparse
import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.csv_solder_ball_probes import saved_map
from tools.equivalent_solder_ball_probes import DEFAULT_OUTPUT, PROFILES
from tools.equivalent_solder_ball_rules import fractions, geometry, material_values, mixture
from tools.floxml_validation.native_suite import read_des
from tools.infer_chip_array_bond_wires_floxml import library_material, provenance
from tools.solder_ball_array_probes import ROOT


def nodes(root):
    materials = {e.findtext("name"): e for e in root.findall("./attributes/materials/*")}
    blocks = {}
    for group in root.findall("./geometry/assembly"):
        name = group.findtext("name")
        if name in {"Solder_ball", "Center_SBall"}:
            assert all(float(group.findtext(f"position/{axis}")) == 0 for axis in "xyz")
            for element in group.findall("./geometry/cuboid"):
                blocks[(name, element.findtext("name"))] = element
    return materials, blocks


def infer_air(archive, solder):
    observations = []
    for identifier in PROFILES:
        path = archive / "baselines" / f"{identifier}.xml"
        values = read_des(path.with_suffix(".des"))
        materials, blocks = nodes(ET.parse(path).getroot())
        block = blocks[("Solder_ball", "solder_ball")]
        material = material_values(materials[block.findtext("material")])
        area = float(block.findtext("size/x")) * float(block.findtext("size/y")) * 1e6
        f = int(values["MD"]) * int(values["ME"]) * math.pi * float(values["b"]) ** 2 / (4 * area)
        rho = (material["rho"] - f * solder["rho"]) / (1 - f)
        cp = (material["rho"] * material["cp"] - f * solder["rho"] * solder["cp"]) / ((1 - f) * rho)
        k = (material["z"] - f * solder["k"]) / (1 - f)
        observations.append({"source": provenance(path), "f": f, "rho": rho, "cp": cp, "k": k})
    # The baselines agree to the shown precision despite cancellation in the air contribution.
    air = {"rho": 1.1614, "cp": 1007.0, "k": 0.0261}
    for observation in observations:
        assert all(math.isclose(observation[key], air[key], rel_tol=1e-9) for key in air)
    return air, observations


def check_run(directory, identifiers):
    path = directory / "run.json"
    run = json.loads(path.read_text(encoding="utf-8"))
    assert run["exit_code"] == 0 and not run["errors"]
    assert set(run["exports"]) == set(identifiers)
    for identifier, digest in run["exports"].items():
        assert provenance(directory / f"{identifier}.xml")["sha256"] == digest
    return {"sources": [provenance(path), provenance(directory / "replay.xml")], "execution": run}


def verify_case(directory, definition, phase, solders, air):
    identifier = definition["id"]
    xml = directory / phase / f"{identifier}.xml"
    saved = xml.with_suffix(".des")
    readback = read_des(saved)
    inputs = definition["des_changes"]
    fallback = bool(inputs["balls"]) or inputs["csvBGA"] == "CHECKED"
    expected_saved = inputs | ({"radio_BGA_modeling": "3"} if fallback else {})
    assert all(readback.get(k) == v for k, v in expected_saved.items())
    model_values = readback.copy()
    if phase == "native":
        model_values["radio_BGA_modeling"] = inputs["radio_BGA_modeling"]
    rows = saved_map(saved)
    assert rows == list(map(tuple, definition["map_rows"]))
    expected = geometry(model_values, rows)
    f = fractions(model_values)
    solder = solders[readback["k_solder"]]
    materials, blocks = nodes(ET.parse(xml).getroot())
    assert set(blocks) == {(b["group"], b["name"]) for b in expected}
    geometry_errors, material_errors, observed, inversion_errors = [], [], [], []
    used_materials = set()
    for block in expected:
        element = blocks[(block["group"], block["name"])]
        origin = [float(element.findtext(f"position/{axis}")) * 1000 for axis in "xyz"]
        size = [float(element.findtext(f"size/{axis}")) * 1000 for axis in "xyz"]
        geometry_errors.extend(abs(a - b) for a, b in zip(origin, block["origin"], strict=True))
        geometry_errors.extend(abs(a - b) for a, b in zip(size, block["size"], strict=True))
        kind = block["kind"]
        material_id = {
            "pure": readback["k_solder"],
            "main": "Solder_ball",
            "center": "centerSolder",
        }[kind]
        assert element.findtext("material") == material_id
        actual = material_values(materials[material_id])
        observed.append(
            {
                "group": block["group"],
                "name": block["name"],
                "origin_mm": origin,
                "size_mm": size,
                "material": material_id,
                "properties": actual,
            }
        )
        if material_id in used_materials:
            continue
        used_materials.add(material_id)
        if kind == "pure":
            target = {"rho": solder["rho"], "cp": solder["cp"], **dict.fromkeys("xyz", solder["k"])}
        else:
            target = mixture(solder, air, f[kind], model_values["radio_BGA_modeling"])
            inversions = [
                (actual["rho"] - air["rho"]) / (solder["rho"] - air["rho"]),
                (actual["z"] - air["k"]) / (solder["k"] - air["k"]),
                (actual["rho"] * actual["cp"] - air["rho"] * air["cp"])
                / (solder["rho"] * solder["cp"] - air["rho"] * air["cp"]),
            ]
            inversion_errors.extend(abs(value - f[kind]) for value in inversions)
        material_errors.extend(
            abs(actual[key] - value) / abs(value) for key, value in target.items()
        )
    max_geometry = max(geometry_errors, default=0)
    max_material = max(material_errors, default=0)
    assert max_geometry < 1e-10 and max_material < 1e-11, (
        identifier,
        phase,
        max_geometry,
        max_material,
    )
    observed.sort(key=lambda b: (b["group"], b["name"]))
    return {
        "id": identifier,
        "phase": phase,
        "sources": [
            provenance(xml),
            provenance(saved),
            provenance(directory / "inputs" / f"{identifier}.des"),
        ],
        "requested_inputs": inputs,
        "saved_mode": readback["radio_BGA_modeling"],
        "input_mode_normalized": inputs["radio_BGA_modeling"] != readback["radio_BGA_modeling"],
        "model_hypothesis_mode": model_values["radio_BGA_modeling"],
        "map_rows": rows,
        "fraction_hypothesis": f,
        "observed_blocks": observed,
        "max_geometry_error_mm": max_geometry,
        "max_material_relative_error": max_material,
        "max_fraction_inversion_error": max(inversion_errors, default=0),
        "numeric_checks": len(geometry_errors) + len(material_errors),
        "unphysical_fraction": any(f[b["kind"]] > 1 for b in expected if b["kind"] != "pure"),
        "passed": True,
    }


def verify(archive, output):
    solders = [
        library_material("solder_alloys/solder_sn63_pb37_ba8a0611.json"),
        library_material("solder_alloys/solder_pb90_sn10_af08e70a.json"),
    ]
    solder_map = {s["name"]: s for s in solders}
    air, calibration = infer_air(archive, solders[0])
    baseline_run = check_run(archive / "baselines", PROFILES)
    profiles, all_cases, roundtrip_changes = {}, [], []
    for identifier, (family, mode) in PROFILES.items():
        directory = archive / identifier
        definition_file = directory / "definitions.json"
        definitions = json.loads(definition_file.read_text(encoding="utf-8"))["cases"]
        reload_definitions = [
            d
            for d in definitions
            if d["des_changes"]["balls"] or d["des_changes"]["csvBGA"] == "CHECKED"
        ]
        native_run = check_run(directory / "native", [d["id"] for d in definitions])
        reload_run = check_run(directory / "reloaded", [d["id"] for d in reload_definitions])
        cases = [verify_case(directory, d, "native", solder_map, air) for d in definitions]
        reloaded = [
            verify_case(directory, d, "reloaded", solder_map, air) for d in reload_definitions
        ]
        native_by_id = {c["id"]: c for c in cases}
        for case in reloaded:
            if case["observed_blocks"] != native_by_id[case["id"]]["observed_blocks"]:
                roundtrip_changes.append(f"{identifier}/{case['id']}")
        profiles[identifier] = {
            "family": family,
            "mode": mode,
            "definitions": provenance(definition_file),
            "native_run": native_run,
            "reload_run": reload_run,
            "cases": cases,
            "reloaded": reloaded,
        }
        all_cases.extend(cases + reloaded)
    summary = {
        "profiles": len(profiles),
        "initial_exports": sum(len(p["cases"]) for p in profiles.values()),
        "reload_exports": sum(len(p["reloaded"]) for p in profiles.values()),
        "baseline_exports": 4,
        "verified_cases": len(all_cases),
        "numeric_checks": sum(c["numeric_checks"] for c in all_cases),
        "max_geometry_error_mm": max(c["max_geometry_error_mm"] for c in all_cases),
        "max_material_relative_error": max(c["max_material_relative_error"] for c in all_cases),
        "max_fraction_inversion_error": max(c["max_fraction_inversion_error"] for c in all_cases),
        "roundtrip_changed_cases": roundtrip_changes,
        "unphysical_fraction_cases": [
            f"{p}/{c['id']}"
            for p, data in profiles.items()
            for c in data["cases"]
            if c["unphysical_fraction"]
        ],
        "all_passed": all(c["passed"] for c in all_cases),
    }
    report = {
        "date": "2026-10-25",
        "scope": "Native orthotropic and WB isotropic solder-ball equivalents",
        "evidence": "Native FloXML, original and saved DES, CSV var2, constituent JSONs; "
        "no production equations or native calculation probes.",
        "solders": solders,
        "air_inferred": air,
        "air_calibration": calibration,
        "baseline_run": baseline_run,
        "summary": summary,
        "profiles": profiles,
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/validation/equivalent_solder_balls_floxml_2026-10-25.json",
    )
    args = parser.parse_args()
    verify(args.archive.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
