from math import ceil, sqrt

from packstudio.domain.enums import StructureType
from packstudio.domain.geometry import AxisAlignedBlock, Point3D, Size3D
from packstudio.templates.cbga_fc.equivalent import create_equivalent_material
from packstudio.templates.package_library.core.builds import LayerBuild
from packstudio.templates.package_library.core.definitions import TemplateValues
from packstudio.templates.package_library.core.materials import material


def build_flip_chip_layer(
    values: TemplateValues,
    footprint_x: float,
    footprint_y: float,
    base_z: float,
) -> LayerBuild:
    total = values.integer("bumps.total")
    diameter = values.number("bumps.diameter")
    height = values.number("bumps.height")
    columns = max(1, ceil(sqrt(total * footprint_x / footprint_y)))
    cell_area = footprint_x * footprint_y / total
    pitch_x = footprint_x / columns
    pitch_y = cell_area / pitch_x
    solder = material("solder-pb90")
    underfill = material("underfill")
    equivalent, properties = create_equivalent_material(
        material_id="flip-chip-bumps-equivalent",
        name="Flip-chip bumps + underfill orthotropic equivalent",
        element=solder,
        matrix=underfill,
        radius=diameter / 2,
        pitch_x=pitch_x,
        pitch_y=pitch_y,
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
            "tensor": "orthotropic",
            "fill_fraction": properties.fill_fraction,
            "physical_elements": total,
        },
    )
    return LayerBuild(
        blocks=[block],
        materials=[solder, underfill, equivalent],
        group_names={"group-flip-chip-bumps": "Flip-chip bumps + underfill"},
        metadata={
            "flip_chip_bump_count": total,
            "flip_chip_bump_representation": "thick_orthotropic_equivalent",
            "flip_chip_bump_footprint_x_mm": footprint_x,
            "flip_chip_bump_footprint_y_mm": footprint_y,
        },
    )
