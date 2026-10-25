"""Infer wire count from freshly exported FloXML, independently of emitted ball count."""

import argparse
import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.chip_array_ball_count_probes import DEFAULT_OUTPUT, ROOT
from tools.floxml_validation.native_suite import read_des
from tools.infer_chip_array_bond_wires_floxml import (
    library_material,
    material_values,
    provenance,
)


def balls(root):
    group = next(
        a for a in root.findall("./geometry/assembly") if a.findtext("name") == "Solder_ball"
    )
    return group.findall("./geometry/cuboid")


def verify_case(definition, directory, axes, metal, matrix):
    identifier = definition["id"]
    path = directory / "native" / f"{identifier}.xml"
    root = ET.parse(path).getroot()
    des_path = path.with_suffix(".des")
    readback = read_des(des_path)
    assert all(readback.get(k) == v for k, v in definition["des_changes"].items())
    ball_cubes = balls(root)
    # DES row zero is the upper edge; FloXML's physical y axis points upward.
    cells = sorted(
        (
            axes[0].index(round(float(e.findtext("position/x")), 12)),
            len(axes[1]) - 1 - axes[1].index(round(float(e.findtext("position/y")), 12)),
        )
        for e in ball_cubes
    )
    assert cells == [tuple(cell) for cell in definition["expected_geometry_cells"]]
    cubes = {e.findtext("name"): e for e in root.findall(".//cuboid")}
    wires = {name: e for name, e in cubes.items() if name.startswith("bw_")}
    assert len(wires) == 8
    for name, element in wires.items():
        expected = "bondwire1" if name.endswith(("right", "left")) else "bondwire2"
        assert element.findtext("material") == expected
    length = float(cubes["die"].findtext("size/x"))
    width = float(cubes["die"].findtext("size/y"))
    diameter = float(wires["bw_h_right"].findtext("size/z"))
    multiplier = 8 * (length + width) / (math.pi * diameter)
    md, me = int(readback["MD"]), int(readback["ME"])
    count = md * me
    if readback["depop_center"] == "CHECKED":
        count -= (md - int(readback["MDp"])) * (me - int(readback["MEp"]))
    if readback["radio_default_bwNumber"] == "2":
        count = int(readback["Nw"])
    assert count == definition["candidate_rule_N"]
    f = count / multiplier
    rho = f * metal["rho"] + (1 - f) * matrix["rho"]
    cp = (f * metal["rho"] * metal["cp"] + (1 - f) * matrix["rho"] * matrix["cp"]) / rho
    parallel = f * metal["k"] + (1 - f) * matrix["k"]
    materials = {e.findtext("name"): e for e in root.findall("./attributes/materials/*")}
    inferred, observed, errors = {}, {}, {}
    for name, axis in (("bondwire1", "x"), ("bondwire2", "y")):
        values = material_values(materials[name])
        observed[name] = values
        inferred[name] = {
            "density": (values["rho"] - matrix["rho"]) / (metal["rho"] - matrix["rho"]),
            "conductivity": (values[axis] - matrix["k"]) / (metal["k"] - matrix["k"]),
            "volumetric_heat_capacity": (
                values["rho"] * values["cp"] - matrix["rho"] * matrix["cp"]
            )
            / (metal["rho"] * metal["cp"] - matrix["rho"] * matrix["cp"]),
        }
        inferred[name] = {
            source: fraction * multiplier for source, fraction in inferred[name].items()
        }
        expected = {
            "rho": rho,
            "cp": cp,
            "z": parallel,
            "x": parallel if axis == "x" else matrix["k"],
            "y": parallel if axis == "y" else matrix["k"],
        }
        errors.update(
            {
                f"{name}.{field}": abs(values[field] - value) / abs(value)
                for field, value in expected.items()
            }
        )
    max_count_error = max(abs(value - count) for v in inferred.values() for value in v.values())
    assert max_count_error < 1e-10 and max(errors.values()) < 1e-11
    return {
        "id": identifier,
        "sources": [
            provenance(path),
            provenance(des_path),
            provenance(directory / "inputs" / f"{identifier}.des"),
        ],
        "readback": {k: readback[k] for k in definition["des_changes"]},
        "central_enabled": definition["central_enabled"],
        "explicit_kept_cell_count": len(definition["explicit_kept_cells"]),
        "emitted_ball_count": len(ball_cubes),
        "emitted_cells": cells,
        "candidate_rule_N": count,
        "N_inferred_from_properties": inferred,
        "union_hypothesis_count": definition["union_hypothesis_count"],
        "observed_materials": observed,
        "relative_errors": errors,
        "max_count_inversion_error": max_count_error,
        "passed": True,
    }


def verify(directory, output):
    definitions_path = directory / "definitions.json"
    definitions = json.loads(definitions_path.read_text(encoding="utf-8"))
    reference = directory / "baseline/fresh.xml"
    baseline = ET.parse(reference).getroot()
    axes = [
        sorted({round(float(e.findtext(f"position/{axis}")), 12) for e in balls(baseline)})
        for axis in "xy"
    ]
    assert tuple(map(len, axes)) == (5, 5)
    metal = library_material("metals/gold_pure_2eb9f2a5.json")
    matrix = library_material("resins/epoxy_overmold_typical_40bee0af.json")
    native_path = directory / "native/run.json"
    native = json.loads(native_path.read_text(encoding="utf-8"))
    assert native["exit_code"] == 0 and not native["errors"]
    assert len(native["exports"]) == len(definitions)
    for identifier, digest in native["exports"].items():
        assert provenance(directory / "native" / f"{identifier}.xml")["sha256"] == digest
    cases = [verify_case(case, directory, axes, metal, matrix) for case in definitions]
    summary = {
        "new_native_exports": len(cases) + 1,
        "probe_cases": len(cases),
        "property_checks": 10 * len(cases),
        "all_passed": all(c["passed"] for c in cases),
        "max_relative_error": max(max(c["relative_errors"].values()) for c in cases),
        "max_count_inversion_error": max(c["max_count_inversion_error"] for c in cases),
        "counterexamples_to_remaining_ball_count": [
            c["id"] for c in cases if c["candidate_rule_N"] != c["emitted_ball_count"]
        ],
        "counterexamples_to_geometry_union": [
            c["id"] for c in cases if c["union_hypothesis_count"] != c["emitted_ball_count"]
        ],
    }
    report = {
        "date": "2026-10-25",
        "scope": "Chip Array actualDie/standardOutline, 5x5 regular grid",
        "evidence": "Fresh native FloXML, input DES and saved DES readback; material JSONs. "
        "No native calculation probes or disassembly used to determine the count rule.",
        "mechanism": "DES balls is an explicit kept-cell list; csvBGA is disabled in every probe.",
        "cell_coordinates": "zero-based DES (column,row); row increases toward negative y",
        "constituents": {"metal": metal, "matrix": matrix},
        "sources": [
            provenance(definitions_path),
            provenance(reference),
            provenance(directory / "native/replay.xml"),
            provenance(native_path),
        ],
        "native_execution": native,
        "summary": summary,
        "cases": cases,
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/validation/chip_array_ball_count_floxml_2026-10-25.json",
    )
    args = parser.parse_args()
    verify(args.archive.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
