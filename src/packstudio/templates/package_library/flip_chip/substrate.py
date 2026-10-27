"""FC PBGA core, metal tables and independent upper/lower build-up regions."""

from math import pi, sqrt

from packstudio.domain.enums import StructureType
from packstudio.domain.materials import ConductivityTensor
from packstudio.templates.package_library.core.geometry import centered_draft
from packstudio.templates.package_library.core.materials import material
from packstudio.templates.package_library.core.metal_layers import append_metal_layers
from packstudio.templates.package_library.core.mixtures import mix_material
from packstudio.templates.package_library.core.via_geometry import via_grid_drafts


def append_substrate(drafts, values, request):
    length, width = values.number("substrate.length"), values.number("substrate.width")
    height, base = values.number("substrate.thickness"), values.number("bga.height")
    top = base + height
    materials = []
    metal = material(request.material_assignments["group-metal"], request.custom_materials)
    matrix = material(request.material_assignments["group-substrate"], request.custom_materials)
    append_metal_layers(
        drafts,
        materials,
        values.table("metal.layers"),
        length,
        width,
        top,
        metal,
        matrix,
        skip_zero_depth=True,
    )
    thicknesses = {}
    for region in ("upper", "lower"):
        thicknesses[region] = 0
        if not values.boolean(region + ".enabled"):
            continue
        if not request.material_assignments["group-" + region]:
            continue
        h = values.number(region + ".thickness")
        thicknesses[region] = h
        z = top - h if region == "upper" else base
        dielectric = material(
            request.material_assignments["group-" + region], request.custom_materials
        )
        drafts.append(
            centered_draft(
                region + "-region",
                region + " region",
                StructureType.SUBSTRATE,
                (length, width, h),
                z,
                dielectric.id,
                "group-" + region,
                region.title() + " region",
            )
        )
        append_metal_layers(
            drafts,
            materials,
            values.table(region + ".layers"),
            length,
            width,
            top,
            metal,
            dielectric,
            region + "trace",
            skip_zero_depth=True,
        )
        if values.is_missing(region + ".count"):
            continue
        diameter = values.number(region + ".diameter")
        shell = (
            1
            if values.boolean(region + ".filled")
            else (1 - ((diameter - 2 * values.number(region + ".plating")) / diameter) ** 2)
        )
        single = hollow_via(metal, shell, region + "-via-single")
        dl, dw = values.number("die.length"), values.number("die.width")
        fraction = values.integer(region + ".count") * pi * diameter**2 / (4 * dl * dw)
        identifier = region + "-microvias"
        equivalent = mix_material(
            single.model_copy(update={"id": identifier}), single, dielectric, fraction, {"z"}
        )
        materials.append(equivalent)
        drafts.append(
            centered_draft(
                identifier,
                identifier,
                StructureType.VIA,
                (dl, dw, h),
                z,
                equivalent.id,
                "group-" + region,
                region.title() + " region",
            )
        )
    if values.boolean("vias.enabled"):
        diameter, plating = values.number("vias.diameter"), values.number("vias.plating")
        if not 0 <= plating <= diameter / 2:
            raise ValueError("通孔镀层厚度必须位于 0 和孔半径之间")
        shell = 1 - ((diameter - 2 * plating) / diameter) ** 2
        single = hollow_via(metal, shell, "fc-core-via")
        z = base + thicknesses["lower"]
        h = height - thicknesses["upper"] - thicknesses["lower"]
        nr, nc = values.integer("vias.rows"), values.integer("vias.columns")
        pitch = values.number("vias.pitch")
        if values.text("vias.modeling") == "discrete":
            materials.append(single)
            drafts.extend(
                via_grid_drafts(
                    "core-via",
                    nr,
                    nc,
                    pitch,
                    sqrt(pi) * diameter / 2,
                    z,
                    h,
                    material_id=single.id,
                    configuration=request.vias,
                    native_row_order=True,
                )
            )
        else:
            lx, ly = (nc - 1) * pitch + diameter, (nr - 1) * pitch + diameter
            omitted = request.vias.omissions(nr, nc) if request.vias else set()
            fraction = (nr * nc - len(omitted)) * pi * diameter**2 / (4 * lx * ly)
            # PACK's core-via branch reads an anisotropic substrate tensor.
            # Isotropic substrates contribute zero conductivity to this branch.
            tensor = matrix.conductivity
            if tensor.x == tensor.y == tensor.z:
                matrix = matrix.model_copy(
                    update={"conductivity": ConductivityTensor(x=0, y=0, z=0)}
                )
            equivalent = mix_material(single, single, matrix, fraction, {"z"})
            materials.append(equivalent)
            drafts.append(
                centered_draft(
                    "core-vias",
                    "Core vias",
                    StructureType.VIA,
                    (lx, ly, h),
                    z,
                    equivalent.id,
                    "group-vias",
                    "Core vias",
                )
            )
    return materials


def hollow_via(metal, shell, identifier):
    return metal.model_copy(
        update={
            "id": identifier,
            "name": identifier,
            "conductivity_coefficient": None,
            "conductivity_reference_temperature_c": None,
            "density": shell * metal.density,
            "conductivity": ConductivityTensor.isotropic(shell * metal.conductivity.z),
        }
    )
