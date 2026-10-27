from math import pi

from packstudio.domain.enums import StructureType
from packstudio.domain.geometry import AxisAlignedBlock, Point3D, Size3D
from packstudio.domain.materials import ConductivityTensor
from packstudio.templates.package_library.core.builds import LayerBuild
from packstudio.templates.package_library.core.definitions import TemplateValues
from packstudio.templates.package_library.core.materials import material
from packstudio.templates.package_library.core.mixtures import mix_material
from packstudio.templates.package_library.core.parameters import TemplateRequest


def build_flip_chip_layer(
    values: TemplateValues,
    footprint_x: float,
    footprint_y: float,
    base_z: float,
    *,
    request: TemplateRequest,
) -> LayerBuild:
    total = (
        values.integer("bumps.columns") * values.integer("bumps.rows")
        if values.matches({"bumps.array_type": "regular"})
        else values.integer("bumps.total")
    )
    diameter = values.number("bumps.diameter")
    height = values.number("bumps.height")
    solder = material(request.material_assignments["group-bump-solder"], request.custom_materials)
    underfill = material(
        request.material_assignments.get("group-underfill", "static-air")
        if not values.matches({"bumps.underfill": False})
        else "static-air",
        request.custom_materials,
    )
    fraction = total * pi * diameter**2 / (4 * footprint_x * footprint_y)
    equivalent = mix_material(
        solder.model_copy(
            update={
                "id": "flip-chip-bumps-equivalent",
                "name": "Flip-chip bumps isotropic equivalent",
            }
        ),
        solder,
        underfill,
        fraction,
        set("xyz"),
    )
    equivalent = equivalent.model_copy(
        update={
            "conductivity": ConductivityTensor.isotropic(equivalent.conductivity.z),
        }
    )
    block = AxisAlignedBlock(
        id="flip-chip-bumps-equivalent",
        name="Flip-chip bumps + underfill equivalent layer",
        structure_type=StructureType.FLIP_CHIP_BUMP,
        origin=Point3D(x=-footprint_x / 2, y=-footprint_y / 2, z=base_z),
        size=Size3D(x=footprint_x, y=footprint_y, z=height),
        material_id=equivalent.id,
        parent_group_id="group-flip-chip-bumps",
        metadata={
            "representation": "equivalent",
            "tensor": "isotropic",
            "fill_fraction": fraction,
            "physical_elements": total,
        },
    )
    return LayerBuild(
        blocks=[block],
        materials=[solder, underfill, equivalent],
        group_names={"group-flip-chip-bumps": "Flip-chip bumps + underfill"},
        metadata={
            "flip_chip_bump_count": total,
            "flip_chip_bump_representation": "thick_isotropic_equivalent",
            "flip_chip_bump_footprint_x_mm": footprint_x,
            "flip_chip_bump_footprint_y_mm": footprint_y,
        },
    )
