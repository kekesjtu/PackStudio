"""PACK QFN discrete hollow vias extend down from the solder seating plane."""

from math import pi, sqrt

from packstudio.domain.materials import ConductivityTensor, Material
from packstudio.templates.package_library.core.definitions import TemplateValues
from packstudio.templates.package_library.core.geometry import DraftBlock
from packstudio.templates.package_library.core.materials import material
from packstudio.templates.package_library.core.parameters import TemplateRequest
from packstudio.templates.package_library.core.via_geometry import via_grid_drafts


def qfn_vias(
    values: TemplateValues, request: TemplateRequest
) -> tuple[list[DraftBlock], list[Material]]:
    if not values.boolean("vias.enabled"):
        return [], []
    diameter, plating = values.number("vias.diameter"), values.number("vias.plating")
    if plating > diameter / 2:
        raise ValueError("via plating must not exceed the via radius")
    if diameter > values.number("vias.pitch"):
        raise ValueError("via diameter must not exceed the pitch")
    for axis, count in (("length", "columns"), ("width", "rows")):
        span = (values.integer(f"vias.{count}") - 1) * values.number("vias.pitch") + diameter
        if span > values.number(f"pad.exposed_{axis}"):
            raise ValueError("QFN vias must fit inside the exposed pad")
    available = {"copper": material("copper")}
    available.update((item.id, item) for item in request.custom_materials)
    metal = available["copper"]
    fraction = 1 - ((diameter - 2 * plating) / diameter) ** 2
    via = metal.model_copy(
        update={
            "id": "qfn-via",
            "name": "QFN hollow via",
            "conductivity": ConductivityTensor.isotropic(fraction * metal.conductivity.x),
            "density": fraction * metal.density,
            "source": f"PACK derived hollow via; metal={metal.id}; shell_fraction={fraction:.16g}",
        }
    )
    # Explicit equivalent overrides have the same precedence as other derived materials.
    via = next((m for m in request.custom_materials if m.id == via.id), via)
    drafts = via_grid_drafts(
        "thermal-via",
        values.integer("vias.rows"),
        values.integer("vias.columns"),
        values.number("vias.pitch"),
        sqrt(pi) * diameter / 2,
        -values.number("vias.length"),
        values.number("vias.length"),
        material_id=via.id,
        configuration=request.vias,
    )
    return drafts, [via]
