"""Compare native exports to public generation with explicit decision exceptions."""

from math import isclose
from xml.etree import ElementTree as ET

from tools.dotnet_core import export_model
from tools.pack_sweep.decisions import decision_geometry
from tools.pack_sweep.geometry import geometry_index


def close(actual, expected):
    return len(actual) == len(expected) and all(
        isclose(a, b, rel_tol=1e-10, abs_tol=1e-8) for a, b in zip(actual, expected, strict=True)
    )


def compare_model(native_path, request):
    return compare_native(ET.parse(native_path).getroot(), request)


def compare_native(native, request):
    family = request["template_id"]
    native = decision_geometry(native, family)
    actual = ET.fromstring(export_model(request))
    expected_shapes, actual_shapes = geometry_index(native), geometry_index(actual)
    if expected_shapes.keys() != actual_shapes.keys():
        raise ValueError(
            f"{family}: cuboid geometry differs; "
            f"missing={list(expected_shapes.keys() - actual_shapes.keys())[:4]}; "
            f"extra={list(actual_shapes.keys() - expected_shapes.keys())[:4]}"
        )
    exceptions = set()
    for shape, entries in expected_shapes.items():
        remaining = actual_shapes[shape].copy()
        for name, properties in entries:
            start = 2 if family == "bare_die" and "bump" in name.lower() else 0
            if start:
                exceptions.add("BGA与Bumps建模表达: Bare Die bump kx/ky")
            match = next(
                (
                    item
                    for item in remaining
                    if (
                        item[1] is None
                        if properties is None
                        else item[1] is not None and close(item[1][start:], properties[start:])
                    )
                ),
                None,
            )
            if match is None:
                raise ValueError(
                    f"{family}: material mismatch at {name}: {properties}, {remaining}"
                )
            remaining.remove(match)
        if remaining:
            raise ValueError(f"{family}: cuboid multiplicity differs at {shape}")
    def laws(root):
        if root.tag == "model":
            return sorted(
                (
                    float(e.find("conductivity").attrib["x"]),
                    float(e.findtext("coefficient")),
                    float(e.findtext("reference_temperature")),
                )
                for e in root.findall("materials/material")
                if e.attrib["type"] == "temperature_dependent"
            )
        return sorted(
            tuple(float(e.findtext(k)) for k in ("conductivity", "coeff", "tref"))
            for e in root.findall("attributes/materials/temperature_dependant_material_att")
        )

    if not close(
        [v for row in laws(native) for v in row], [v for row in laws(actual) for v in row]
    ):
        raise ValueError(f"{family}: temperature-dependent material laws differ")
    power = sum(float(s.findtext("power")) for s in native.findall("attributes/sources/source_att"))
    if not isclose(
        power,
        sum(float(s.attrib["power"]) for s in actual.findall("sources/source")),
        abs_tol=1e-10,
    ):
        raise ValueError(f"{family}: total power differs")
    return {
        "geometry": "passed",
        "materials": "passed",
        "power": "passed",
        "blocks": len(actual.findall("group/block")),
        "decision_policy": family,
        "material_exceptions": sorted(exceptions),
    }
