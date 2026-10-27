"""Retained PACK lead-envelope and QFP tie-bar constitutive rules."""

from math import hypot

from packstudio.domain.materials import ConductivityTensor, Material
from packstudio.templates.package_library.core.definitions import TemplateValues
from packstudio.templates.package_library.core.mixtures import mix_material
from packstudio.templates.package_library.core.parameters import TemplateRequest


def leadframe_materials(
    template: str, values: TemplateValues, request: TemplateRequest, available: dict[str, Material]
) -> list[Material]:
    metal = available[request.material_assignments["group-lead-frame"]]
    mold = available[request.material_assignments["group-encapsulant"]]
    fraction = values.number("leads.width") / values.number("leads.pitch")
    result = []
    for location, matrix in [("inner", mold), ("outer", available["static-air"])]:
        coverage = (
            values.number("leads.coverage") / 100
            if location == "inner" and values.boolean("leads.custom_coverage")
            else fraction
        )
        axes = ["x", "y"] if template == "pqfp" else [None]
        for axis in axes:
            identifier = f"{template}-leadframe-{location}" + (f"-{axis}" if axis else "")
            result.append(
                mix_material(
                    available[identifier],
                    metal,
                    matrix,
                    coverage,
                    {axis, "z"}
                    if axis and values.text("leads.modeling") == "orthotropicCuboid"
                    else set("xyz"),
                )
            )
    if template == "pqfp":
        metal = available[request.material_assignments["group-lead-frame"]]
        a = (values.number("body.length") - values.number("flag.length")) / 2
        b = (values.number("body.width") - values.number("flag.width")) / 2
        if min(a, b) <= 0:
            raise ValueError("QFP tie-bar spans must be positive")
        correction = hypot(a, b) * (1 / a + 1 / b)
        result.append(
            available["pqfp-tie-bar"].model_copy(
                update={
                    "conductivity": ConductivityTensor(
                        x=metal.conductivity.x / correction,
                        y=metal.conductivity.y / correction,
                        z=mold.conductivity.z,
                    ),
                    "density": metal.density,
                    "specific_heat": metal.specific_heat,
                    "source": f"PACK tie-bar geometry factor={correction:.16g}; metal={metal.id};",
                }
            )
        )
    return result
