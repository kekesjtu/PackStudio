"""Infer Chip Array mixtures from archived FloXML and the constituent JSON library only."""

import argparse
import hashlib
import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "flotherm_pack_data/templates/chip_array"
TOLERANCE = 1e-11


def provenance(path):
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def library_material(relative):
    path = ROOT / "default_parameters/materials" / relative
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["conductivity"]["model"] == "constant_isotropic"
    return {
        "name": raw["name"],
        "rho": raw["density"]["value"],
        "cp": raw["specific_heat"]["value"],
        "k": raw["conductivity"]["value"],
        "source": provenance(path),
    }


def material_values(element):
    scalar = element.findtext("conductivity")
    if element.tag == "biaxial_material_att":
        scalar = element.findtext("in_plane_conductivity")
        assert float(scalar) == float(element.findtext("normal_conductivity"))
    return {
        "rho": float(element.findtext("density")),
        "cp": float(element.findtext("specific_heat")),
        **{
            axis: float(scalar if scalar is not None else element.findtext(f"{axis}_conductivity"))
            for axis in "xyz"
        },
    }


def count_state(root, script, baseline_footprint):
    edits = {
        e.attrib["property_name"]: e.attrib["new_value"]
        for e in script.findall("./modify_component")
    }
    footprint = script.find("./new_package/new_value[@property_name='jedecFootprint']")
    ball_group = next(
        (a for a in root.findall("./geometry/assembly") if a.findtext("name") == "Solder_ball"),
        None,
    )
    balls = [] if ball_group is None else ball_group.findall("./geometry/cuboid")
    md, me = 5, 5  # Baseline FloXML has five distinct positions on each axis.
    if footprint.attrib["new_value"] != baseline_footprint:
        md, me = (len({b.findtext(f"position/{axis}") for b in balls}) for axis in "xy")
        assert md * me == len(balls), "changed footprint must have a full rectangular grid"
    md = int(edits.get("numberOfSolderBallsInXMD", md))
    me = int(edits.get("numberOfSolderBallsInYME", me))
    rule = "rectangular_parameter_count"
    count = md * me
    if edits.get("depopulatedCenter") == "true":
        mdp = int(edits["numberFullyPopulatedRowsMDp"])
        mep = int(edits["numberFullyPopulatedRowsMEp"])
        count -= (md - mdp) * (me - mep)
        rule = "rectangular_parameter_count_minus_center"
    if edits.get("solderBallMap") == "true":
        assert not balls, "only the archived empty-map case is covered"
        count, rule = 0, "empty_enabled_ball_map"
    if edits.get("numberBondWiresEqualsSolderBalls") == "no":
        count = int(edits["numberOfBondWiresNw"])
        rule = "explicit_wire_count_from_input_script"
    return {
        "N": count,
        "MD": md,
        "ME": me,
        "rule": rule,
        "emitted_ball_cuboids": len(balls),
        "edits": edits,
    }


def read_case(path, baseline_footprint):
    root = ET.parse(path).getroot()
    script_path = path.with_name("script.xml")
    script = ET.parse(script_path).getroot()
    initial = {
        e.attrib["property_name"]: e.attrib["new_value"]
        for e in script.findall("./new_package/new_value")
    }
    case_id = path.parent.name
    if initial.get("dieType") != "actualDie":
        return None, {"id": case_id, "reason": "thermalDie is a different branch"}
    if initial.get("outlineType") != "standardOutline":
        return None, {"id": case_id, "reason": "nonstandard outline is outside scope"}
    materials = {e.findtext("name"): e for e in root.findall("./attributes/materials/*")}
    if "bondwire1" not in materials:
        return None, {"id": case_id, "reason": "Bond Wires ignored; no mixture emitted"}
    cubes = {e.findtext("name"): e for e in root.findall(".//cuboid")}
    wires = {name: e for name, e in cubes.items() if name.startswith("bw_")}
    assert len(wires) == 8
    for name, element in wires.items():
        expected = "bondwire1" if name.endswith(("right", "left")) else "bondwire2"
        assert element.findtext("material") == expected
    dimensions = {
        "Ld": float(cubes["die"].findtext("size/x")) * 1000,
        "Wd": float(cubes["die"].findtext("size/y")) * 1000,
        "d": float(wires["bw_h_right"].findtext("size/z")) * 1000,
    }
    return {
        "id": case_id,
        "sources": [provenance(path), provenance(script_path)],
        "inputs": {**dimensions, **count_state(root, script, baseline_footprint)},
        "observed": {name: material_values(materials[name]) for name in ("bondwire1", "bondwire2")},
        "matrix_in_xml": material_values(materials["Epoxy Overmold (Typical)"]),
    }, None


def infer_and_check(case, metal, matrix):
    inputs = case["inputs"]
    f = inputs["N"] * math.pi * inputs["d"] / (8 * (inputs["Ld"] + inputs["Wd"]))
    rho = f * metal["rho"] + (1 - f) * matrix["rho"]
    cp = (f * metal["rho"] * metal["cp"] + (1 - f) * matrix["rho"] * matrix["cp"]) / rho
    parallel = f * metal["k"] + (1 - f) * matrix["k"]
    for field, value in (
        ("rho", matrix["rho"]),
        ("cp", matrix["cp"]),
        ("x", matrix["k"]),
        ("y", matrix["k"]),
        ("z", matrix["k"]),
    ):
        assert math.isclose(case["matrix_in_xml"][field], value, rel_tol=TOLERANCE)
    inversions, errors, predicted = {}, {}, {}
    for name, axis in (("bondwire1", "x"), ("bondwire2", "y")):
        observed = case["observed"][name]
        inferred = {
            "density": (observed["rho"] - matrix["rho"]) / (metal["rho"] - matrix["rho"]),
            "conductivity": (observed[axis] - matrix["k"]) / (metal["k"] - matrix["k"]),
            "volumetric_heat_capacity": (
                observed["rho"] * observed["cp"] - matrix["rho"] * matrix["cp"]
            )
            / (metal["rho"] * metal["cp"] - matrix["rho"] * matrix["cp"]),
        }
        expected = {
            "rho": rho,
            "cp": cp,
            "z": parallel,
            "x": parallel if axis == "x" else matrix["k"],
            "y": parallel if axis == "y" else matrix["k"],
        }
        predicted[name] = expected
        for field, value in expected.items():
            errors[f"{name}.{field}"] = abs(observed[field] - value) / max(abs(value), 1e-30)
        inversions[name] = inferred
    coefficient = (
        (
            inversions["bondwire1"]["density"]
            * (inputs["Ld"] + inputs["Wd"])
            / (inputs["N"] * inputs["d"])
        )
        if inputs["N"]
        else None
    )
    case.update(
        f=f,
        coefficient_from_density=coefficient,
        fractions_inverted=inversions,
        predicted=predicted,
        relative_errors=errors,
        max_fraction_error=max(abs(value - f) for v in inversions.values() for value in v.values()),
        passed=max(errors.values()) < TOLERANCE,
    )
    volume_cp = f * metal["cp"] + (1 - f) * matrix["cp"]
    series_k = 1 / (f / metal["k"] + (1 - f) / matrix["k"])
    case["alternative_absolute_errors"] = {
        "volume_weighted_specific_heat": abs(volume_cp - case["observed"]["bondwire1"]["cp"]),
        "series_conductivity": abs(series_k - case["observed"]["bondwire1"]["x"]),
        "metal_only_conductivity": abs(f * metal["k"] - case["observed"]["bondwire1"]["x"]),
    }


def analyze():
    metal = library_material("metals/gold_pure_2eb9f2a5.json")
    matrix = library_material("resins/epoxy_overmold_typical_40bee0af.json")
    baseline = ARCHIVE / "baseline/model.xml"
    baseline_script = ET.parse(baseline.with_name("script.xml")).getroot()
    baseline_root = ET.parse(baseline).getroot()
    ball_group = next(
        a
        for a in baseline_root.findall("./geometry/assembly")
        if a.findtext("name") == "Solder_ball"
    )
    assert tuple(
        len({b.findtext(f"position/{axis}") for b in ball_group.findall("./geometry/cuboid")})
        for axis in "xy"
    ) == (5, 5)
    footprint = baseline_script.find(
        "./new_package/new_value[@property_name='jedecFootprint']"
    ).attrib["new_value"]
    paths = [baseline, *sorted((ARCHIVE / "xml_variations").glob("*/*/model.xml"))]
    cases, excluded = [], []
    for path in paths:
        case, omission = read_case(path, footprint)
        if omission:
            excluded.append(omission)
            continue
        infer_and_check(case, metal, matrix)
        cases.append(case)
    calibration_ids = {
        "baseline",
        "par_v2_c029_bondwirediameterdw_0_0225",
        "par_v2_c013_dielengthld_1_08",
        "par_v2_c039_numberofsolderballsinxmd_4",
    }
    calibration = [c for c in cases if c["id"] in calibration_ids]
    coefficient = sum(c["coefficient_from_density"] for c in calibration) / len(calibration)
    assert len(calibration) == 4 and math.isclose(coefficient, math.pi / 8, rel_tol=TOLERANCE)
    for case in cases:
        case["role"] = "calibration" if case["id"] in calibration_ids else "cross_validation"
    by_id = {case["id"]: case for case in cases}
    powers = {}
    for low, high, variable in (
        ("par_v2_c029_bondwirediameterdw_0_0225", "par_v2_c030_bondwirediameterdw_0_0275", "d"),
        ("par_v2_c039_numberofsolderballsinxmd_4", "par_v2_c040_numberofsolderballsinxmd_6", "N"),
    ):
        a, b = by_id[low], by_id[high]
        powers[variable] = math.log(
            b["fractions_inverted"]["bondwire1"]["density"]
            / a["fractions_inverted"]["bondwire1"]["density"]
        ) / math.log(b["inputs"][variable] / a["inputs"][variable])
    summary = {
        "cases": len(cases),
        "calibration_cases": len(calibration),
        "cross_validation_cases": len(cases) - len(calibration),
        "material_property_checks": 10 * len(cases),
        "passed_cases": sum(c["passed"] for c in cases),
        "coefficient_from_calibration": coefficient,
        "pi_over_8": math.pi / 8,
        "powers_from_density_inversion": powers,
        "max_relative_error": max(max(c["relative_errors"].values()) for c in cases),
        "max_fraction_inversion_error": max(c["max_fraction_error"] for c in cases),
        "count_discrepancies": [
            {
                "id": c["id"],
                "N": c["inputs"]["N"],
                "emitted_ball_cuboids": c["inputs"]["emitted_ball_cuboids"],
            }
            for c in cases
            if c["inputs"]["N"] != c["inputs"]["emitted_ball_cuboids"]
        ],
    }
    return {
        "scope": "Chip Array, actualDie, standardOutline; archived FloXML only",
        "evidence_policy": "Only model.xml, its input script.xml, and two material JSONs; "
        "no production formulas, native probes, or DLL disassembly.",
        "units": {"length": "mm", "k": "W/(m*K)", "rho": "kg/m^3", "cp": "J/(kg*K)"},
        "constituents": {"metal": metal, "matrix": matrix},
        "summary": summary,
        "excluded": excluded,
        "cases": cases,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/validation/chip_array_bond_wire_floxml_inference.json",
    )
    args = parser.parse_args()
    report = analyze()
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["summary"], ensure_ascii=True, indent=2))
    if report["summary"]["passed_cases"] != report["summary"]["cases"]:
        raise SystemExit("FloXML formula cross-validation failed; inspect the report")


if __name__ == "__main__":
    main()
