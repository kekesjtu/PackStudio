"""Chip Array trace tables and ball-grid-coupled accurate/approximate vias."""

from math import pi, sqrt

from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.bga.native_solder import main_cells
from packstudio.templates.package_library.core.geometry import centered_draft
from packstudio.templates.package_library.core.materials import material
from packstudio.templates.package_library.core.metal_layers import append_metal_layers
from packstudio.templates.package_library.core.mixtures import mix_material


def append_details(drafts, values, request):
    length, width = values.number("package.length"), values.number("package.width")
    base, height = values.number("bga.height"), values.number("substrate.thickness")
    top = base + height
    metal = material(request.material_assignments["group-metal"], request.custom_materials)
    matrix = material(request.material_assignments["group-substrate"], request.custom_materials)
    rows = values.table("metal.layers")
    if len(rows) < 2:
        raise ValueError("Chip Array 金属层表需要顶层和底层")
    if f"{request.template_id}.metal.layers" not in request.overrides:
        rows[0]["thickness"] = values.number("trace.top_thickness")
        rows[-1]["thickness"] = values.number("trace.bottom_thickness")
    rows[0]["depth"] = 0
    rows[-1]["depth"] = height - rows[-1]["thickness"]
    materials = []
    append_metal_layers(drafts, materials, rows, length, width, top, metal, matrix)
    if not values.is_missing("metal.hole_length") and not values.is_missing("metal.hole_width"):
        drafts.append(
            centered_draft(
                "trace-hole",
                "Top trace hole",
                StructureType.TRACE,
                (
                    values.number("metal.hole_length"),
                    values.number("metal.hole_width"),
                    rows[0]["thickness"],
                ),
                top - rows[0]["thickness"],
                request.material_assignments["group-trace-hole"],
                "group-traces",
                "Dielectric & traces",
            )
        )
    if not values.boolean("vias.enabled"):
        return materials
    diameter = values.number("vias.diameter")
    filled = values.boolean("vias.filled")
    plating = 0 if filled else values.number("vias.plating")
    if not 0 <= plating <= diameter / 2:
        raise ValueError("via plating must not exceed the via radius")
    shell = 1 if filled else 1 - ((diameter - 2 * plating) / diameter) ** 2
    air = material("static-air", request.custom_materials)
    single = mix_material(
        metal.model_copy(update={"id": "chip-array-via", "name": "Chip Array via"}),
        metal,
        air,
        shell,
        set("xyz"),
    )
    approximate = values.text("vias.modeling") == "approximate"
    b = values.number("bga.diameter") if approximate else diameter
    if approximate:
        single = mix_material(single, single, matrix, diameter**2 / b**2, set("xyz"))
    materials.append(single)
    pitch = values.number("bga.pitch")
    nr, nc = values.integer("bga.rows"), values.integer("bga.columns")
    via_height = height - rows[0]["thickness"] - rows[-1]["thickness"]
    offset_x = 0 if approximate else values.number("vias.offset_x")
    offset_y = 0 if approximate else values.number("vias.offset_y")
    side = sqrt(pi) * b / 2
    for r, c in main_cells(request.bga, nr, nc):
        drafts.append(
            centered_draft(
                f"thermal-via-r{r + 1}-c{c + 1}",
                f"Via {r + 1},{c + 1}",
                StructureType.VIA,
                (side, side, via_height),
                base + rows[-1]["thickness"],
                single.id,
                "group-vias",
                "Vias",
                center_x=(c - (nc - 1) / 2) * pitch + offset_x,
                center_y=(r - (nr - 1) / 2) * pitch + offset_y,
            )
        )
    return materials
