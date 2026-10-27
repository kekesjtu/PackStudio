"""PACK's parameter-derived material rules for the retained cuboid branches."""

from math import pi

from packstudio.domain.materials import Material
from packstudio.templates.package_library.bga.native_solder import wire_count
from packstudio.templates.package_library.core.definitions import TemplateValues
from packstudio.templates.package_library.core.leadframe_materials import leadframe_materials
from packstudio.templates.package_library.core.mixtures import mix_material
from packstudio.templates.package_library.core.parameters import TemplateRequest


def coupled_materials(
    template_id: str,
    values: TemplateValues,
    request: TemplateRequest,
    available: dict[str, Material],
) -> list[Material]:
    if template_id not in {"pbga_wb", "chip_array", "pqfp", "sop"}:
        return []

    def component(group: str) -> Material:
        return available[request.material_assignments[group]]

    matrix = component("group-encapsulant")
    wire = component("group-bond-wires")
    diameter = values.number("bond_wire.diameter")
    die_length, die_width = values.number("die.length"), values.number("die.width")
    prefix = (
        "wirebond"
        if template_id == "pbga_wb"
        else "chip-array"
        if template_id == "chip_array"
        else template_id
    )
    fractions = {}
    if template_id in {"pbga_wb", "sop", "chip_array"}:
        if template_id == "chip_array":
            # This native branch follows the solder-ball count; explicit omission
            # composition remains the project's separate BGA modeling policy.
            count = (
                wire_count(request.bga, values.integer("bga.rows"), values.integer("bga.columns"))
                if values.boolean("bond_wire.auto_count")
                else values.integer("bond_wire.total")
            )
        else:
            count = values.integer(
                "bond_wire.total" if template_id == "pbga_wb" else "bond_wire.count"
            )
        fraction = count * pi * diameter / (8 * (die_length + die_width))
        fractions = {"x": fraction, "y": fraction}
    elif template_id == "pqfp":
        count = values.integer("bond_wire.count")
        perimeter = 2 * (die_length + die_width)
        vertical = abs(
            values.number("die.thickness")
            + values.number("die.attach")
            - values.number("flag.downset")
        )
        for axis, transverse in (("x", die_width), ("y", die_length)):
            die_axis = die_length if axis == "x" else die_width
            flag_axis = values.number("flag.length" if axis == "x" else "flag.width")
            span = (flag_axis - die_axis) / 2 + values.number(f"leads.gap_{axis}") + vertical
            side_count = int(count * transverse / perimeter)
            fractions[axis] = (
                side_count
                * pi
                * diameter**2
                / 4
                * values.number(f"bond_wire.length_{axis}")
                / (span * transverse * diameter)
            )
    result = []
    for axis, fraction in fractions.items():
        identifier = f"{prefix}-bondwire-{axis}"
        parallel = (
            set("xyz")
            if template_id != "chip_array"
            and values.text("bond_wire.modeling") == "isotropicCuboid"
            else {axis, "z"}
        )
        result.append(mix_material(available[identifier], wire, matrix, fraction, parallel))
    if template_id in {"pqfp", "sop"}:
        result.extend(leadframe_materials(template_id, values, request, available))
        metal = component("group-die-flag" if template_id == "sop" else "group-lead-frame")
        fraction = values.number("flag.coverage") / 100
        result.append(
            mix_material(
                available[f"{template_id}-die-flag"],
                metal,
                matrix,
                fraction,
                set("xyz"),
                include_matrix_conductivity=False,
            )
        )
    return result
