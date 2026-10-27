"""QFN board-side vias use copper and a fixed native background medium."""

from packstudio.domain.materials import ConductivityTensor
from packstudio.templates.package_library.core.hollow_vias import hollow_vias
from packstudio.templates.package_library.core.materials import material


def qfn_vias(values, request):
    if not values.boolean("vias.enabled"):
        return [], []
    diameter = values.number("vias.diameter")
    for axis, count in (("length", "columns"), ("width", "rows")):
        span = (values.integer(f"vias.{count}") - 1) * values.number("vias.pitch")
        span += diameter
        if span > values.number(f"pad.exposed_{axis}"):
            raise ValueError("QFN vias must fit inside the exposed pad")
    matrix = material("static-air").model_copy(update={
        "conductivity": ConductivityTensor.isotropic(0.32),
        "density": 1200.0, "specific_heat": 880.0,
    })
    height = values.number("vias.length")
    return hollow_vias(values, request, material("copper", request.custom_materials),
                       matrix, "qfn-via", -height, height)
