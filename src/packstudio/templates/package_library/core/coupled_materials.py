"""PACK's parameter-derived material rules for the retained cuboid branches."""

from math import pi

from packstudio.domain.materials import ConductivityTensor, Material
from packstudio.preset_catalog import PresetCatalog
from packstudio.templates.package_library.bga.native_solder import wire_count
from packstudio.templates.package_library.core.definitions import TemplateValues
from packstudio.templates.package_library.core.leadframe_materials import leadframe_materials
from packstudio.templates.package_library.core.materials import material_id_for_name
from packstudio.templates.package_library.core.mixtures import mix_material
from packstudio.templates.package_library.core.parameters import TemplateRequest
from packstudio.templates.package_library.core.wirebond_copper import wirebond_copper


def coupled_materials(
    template_id: str,
    values: TemplateValues,
    request: TemplateRequest,
    available: dict[str, Material],
) -> list[Material]:
    if template_id not in {"pbga_wb", "chip_array", "pqfp", "sop", "qfn"}:
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
    else:
        for axis, transverse_axis in (("x", "y"), ("y", "x")):
            if values.is_missing(f"leads.count_{transverse_axis}"):
                continue
            count = values.integer(f"leads.count_{transverse_axis}")
            if not count:
                continue
            transverse = (count - 1) * values.number(
                f"leads.pitch_{transverse_axis}"
            ) + values.number("leads.width")
            package_axis = values.number("package.length" if axis == "x" else "package.width")
            die_axis = die_length if axis == "x" else die_width
            span = (
                (package_axis - die_axis) / 2
                - values.number("leads.length")
                - values.number("leads.etch")
            )
            fractions[axis] = (
                count
                * pi
                * diameter**2
                / 4
                * values.number(f"bond_wire.length_{axis}")
                / (span * transverse * diameter)
            )
    result = []
    for axis, fraction in fractions.items():
        identifier = f"{prefix}-bondwire-{axis}"
        result.append(mix_material(available[identifier], wire, matrix, fraction, {axis, "z"}))
    if template_id in {"pqfp", "sop"}:
        result.extend(leadframe_materials(template_id, values, request, available))
        metal = component("group-die-flag")
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
    if template_id == "pbga_wb":
        branch = PresetCatalog().read_branch(values.text("footprint.size"))
        result.extend(wirebond_copper(branch, request, available))
    if template_id == "pbga_wb" and values.boolean("vias.enabled"):
        branch = PresetCatalog().read_branch(values.text("footprint.size"))
        name = branch["groups"]["metalLayers"]["properties"]["materialOfMetal"]["value"]
        metal = available[material_id_for_name(name)]
        diameter, plating = values.number("vias.diameter"), values.number("vias.plating")
        if plating > diameter / 2:
            raise ValueError("via plating must not exceed the via radius")
        fraction = 1 - ((diameter - 2 * plating) / diameter) ** 2
        original = available["wirebond-via"]
        result.append(
            original.model_copy(
                update={
                    "conductivity": ConductivityTensor.isotropic(fraction * metal.conductivity.x),
                    "density": fraction * metal.density,
                    "specific_heat": metal.specific_heat,
                    "source": f"PACK derived hollow via; metal={metal.id}; "
                    f"shell_fraction={fraction:.16g}",
                }
            )
        )
    return result
