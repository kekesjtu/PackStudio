"""Save numeric evidence for retained material couplings against FloXML and DLL helpers."""

import argparse
import hashlib
from pathlib import Path
from xml.etree import ElementTree

from packstudio.templates.package_library.catalog import default_request, generate
from packstudio.templates.package_library.core.materials import material
from tests.backend.templates.reference_requests import reference_request
from tests.backend.templates.test_pack_material_couplings import MATERIALS, cases
from tools.pack_catalog_builder import write_json
from tools.pack_native import VERIFIED_BINARIES
from tools.pack_native_details import EXTRA_BINARIES
from tools.pack_native_formula_probe import NativeFormulaProbe


def attributes(item) -> dict:
    return {
        "conductivity": {
            axis: float(item.findtext("conductivity", item.findtext(f"{axis}_conductivity")))
            for axis in "xyz"
        },
        "density": float(item.findtext("density")),
        "specific_heat": float(item.findtext("specific_heat")),
    }


def actual_attributes(item) -> dict:
    return {
        "conductivity": item.conductivity.model_dump(),
        "density": item.density,
        "specific_heat": item.specific_heat,
    }


def require_close(expected: dict, actual: dict) -> None:
    for key, value in expected.items():
        if isinstance(value, dict):
            require_close(value, actual[key])
        elif abs(actual[key] - value) > max(abs(value) * 1e-11, 1e-12):
            raise ValueError(f"material mismatch: {key}: {actual[key]} != {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installation", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    archived = []
    for case in cases():
        template, field, value, path = case.values
        model = generate(reference_request(template, {f"{template}.{field}": value}))
        original = {
            m.findtext("name"): m
            for m in ElementTree.parse(path).getroot().find("./attributes/materials")
        }
        actual = {m.id: m for m in model.materials}
        checks = []
        for identifier, name in MATERIALS[template].items():
            expected, observed = attributes(original[name]), actual_attributes(actual[identifier])
            require_close(expected, observed)
            checks.append(
                {
                    "material_id": identifier,
                    "floxml_name": name,
                    "expected": expected,
                    "actual": observed,
                }
            )
        archived.append(
            {
                "template": template,
                "field": field,
                "value": value,
                "path": path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "checks": checks,
            }
        )
    native = NativeFormulaProbe(args.installation)
    native_checks = []
    for count, length, diameter in ((32, 2, 0.03), (31, 2.2, 0.03), (40, 1.8, 0.033)):
        request = default_request("pqfp").model_copy(
            update={
                "overrides": {
                    "pqfp.bond_wire.count": count,
                    "pqfp.bond_wire.length_x": length,
                    "pqfp.bond_wire.diameter": diameter,
                }
            }
        )
        actual = next(m for m in generate(request).materials if m.id == "pqfp-bondwire-x")
        expected = native.wire(
            0.978,
            2.1,
            diameter,
            diameter,
            length,
            int(count / 4),
            material("gold"),
            material("epoxy-mold"),
        )
        observed = {
            "conductivity": actual.conductivity.x,
            "density": actual.density,
            "specific_heat": actual.specific_heat,
        }
        require_close(expected, observed)
        native_checks.append(
            {
                "helper_rva": "0x1ccf0",
                "count": count,
                "length": length,
                "diameter": diameter,
                "expected": expected,
                "actual": observed,
            }
        )
    for plating in (0.015, 0.0225, 0.0275, 0.04):
        request = default_request("chip_array").model_copy(
            update={"overrides": {"chip_array.vias.plating": plating}}
        )
        actual = next(m for m in generate(request).materials if m.id == "chip-array-via")
        expected = native.plated_via(
            0.2 - 2 * plating, 0.2, 0.2, material("copper"), material("bt")
        )
        observed = {
            "conductivity": actual.conductivity.x,
            "density": actual.density,
            "specific_heat": actual.specific_heat,
        }
        require_close(expected, observed)
        native_checks.append(
            {"helper_rva": "0x1d350", "plating": plating, "expected": expected, "actual": observed}
        )
    binary = native.binaries["flopackrealise.dll"]
    disassembly = [
        {"rva": hex(rva), "instructions": [binary.annotate(i) for i in binary.instructions(rva)]}
        for rva in (
            0x1CCF0,
            0x1CE70,
            0x1CEB0,
            0x1D350,
            0x2080,
            0x9620,
            0x7CB0,
            0x478A0,
            0x4D9C0,
            0x4EEB0,
            0x34CD0,
            0x35770,
        )
    ]
    write_json(
        root / "docs/validation/pack_material_couplings.json",
        {
            "schema_version": "packstudio.material-coupling-verification/v1",
            "review_date": "2026-10-12",
            "binary_sha256": VERIFIED_BINARIES | EXTRA_BINARIES,
            "archive_cases": archived,
            "native_math_cases": native_checks,
            "scope": "11 fields, 22 archived single-variable cases, 7 native scalar cases; "
            "not a full native geometry realization or exhaustive combination replay.",
        },
    )
    write_json(
        root / "docs/validation/pack_material_rule_disassembly.json",
        {
            "binary_sha256": binary.sha256,
            "functions": disassembly,
        },
    )
    print(f"{len(archived)} FloXML cases and {len(native_checks)} native math cases passed")


if __name__ == "__main__":
    main()
