"""QFN stepped wire envelopes and their local wire volume fractions."""

from math import pi

from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.core.geometry import corner_draft
from packstudio.templates.package_library.core.materials import material
from packstudio.templates.package_library.core.mixtures import mix_material


def qfn_wires(values, request, die_top, lead_top):
    drafts, materials = [], []
    diameter = values.number("bond_wire.diameter")
    steps = values.integer("bond_wire.steps")
    wire = material(request.material_assignments["group-bond-wires"], request.custom_materials)
    matrix = material(request.material_assignments["group-encapsulant"], request.custom_materials)
    for axis, transverse_axis in (("x", "y"), ("y", "x")):
        if values.is_missing(f"leads.count_{transverse_axis}"):
            continue
        count = values.integer(f"leads.count_{transverse_axis}")
        if count == 0:
            continue
        die_axis = values.number("die.length" if axis == "x" else "die.width")
        die_transverse = values.number("die.width" if axis == "x" else "die.length")
        extent = (count - 1) * values.number(f"leads.pitch_{transverse_axis}")
        extent += values.number("leads.width")
        end = values.number("package.length" if axis == "x" else "package.width") / 2
        end -= values.number("leads.length") + values.number("leads.etch")
        span = end - die_axis / 2
        if span <= 0:
            raise ValueError("QFN wire pads must extend beyond the die")

        def equivalent(identifier, transverse, count=count, axis=axis, span=span):
            fraction = count * pi * diameter * values.number(f"bond_wire.length_{axis}")
            fraction /= 4 * span * transverse
            result = mix_material(
                wire.model_copy(update={"id": identifier, "name": identifier}),
                wire,
                matrix,
                fraction,
                {axis, "z"},
            )
            materials.append(result)
            return identifier

        def pair(identifier, start, radial, transverse, z, height, material_id, axis=axis):
            for sign in (-1, 1):
                position = start if sign == 1 else -start - radial
                origin = (position, -transverse / 2, z)
                size = (radial, transverse, height)
                if axis == "y":
                    origin = (origin[1], origin[0], z)
                    size = (size[1], size[0], height)
                drafts.append(
                    corner_draft(
                        f"{identifier}-{sign}",
                        identifier,
                        StructureType.BOND_WIRE,
                        origin,
                        size,
                        material_id,
                        "group-bond-wires",
                        "Bond wires",
                    )
                )

        for index in range(steps):
            transverse = (
                extent
                if steps == 1
                else (die_transverse + index * (extent - die_transverse) / (steps - 1))
            )
            identifier = f"qfn-bondwire-{axis}" + (f"-{index}" if index < steps - 1 else "")
            pair(
                identifier,
                die_axis / 2 + index * span / steps,
                span / steps,
                transverse,
                die_top - diameter,
                diameter,
                equivalent(identifier, transverse),
            )
        height = die_top - lead_top
        if height > 0:
            identifier = f"qfn-bondwire-{axis}-v"
            pair(identifier, end, diameter, extent, lead_top, height, f"qfn-bondwire-{axis}")
    return drafts, materials
