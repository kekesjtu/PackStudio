from dataclasses import dataclass

from packstudio.domain.enums import StructureType
from packstudio.domain.geometry import AxisAlignedBlock, Point3D, Size3D
from packstudio.domain.materials import Material
from packstudio.templates.flip_chip_cbga.parameters import FlipChipCbgaParameters


@dataclass(frozen=True)
class BuiltTopStack:
    blocks: list[AxisAlignedBlock]
    materials: list[Material]
    top_surface_block_ids: list[str]


def build_top_stack(
    parameters: FlipChipCbgaParameters,
    die_top_z: float,
    group_id: str,
) -> BuiltTopStack:
    blocks: list[AxisAlignedBlock] = []
    materials: list[Material] = []
    current_z = die_top_z
    current_length = parameters.die.length
    current_width = parameters.die.width
    top_surface_block_ids = ["die"]

    if parameters.heat_slug.enabled:
        interface = _interface_block(
            block_id="die-to-slug-interface",
            name="Die to heat-slug interface",
            length=current_length,
            width=current_width,
            thickness=parameters.heat_slug.interface_thickness,
            base_z=current_z,
            material=parameters.heat_slug.interface_material,
            group_id=group_id,
        )
        blocks.append(interface)
        materials.append(parameters.heat_slug.interface_material)
        current_z = interface.max_z
        slug = AxisAlignedBlock(
            id="heat-slug",
            name="Embedded heat slug",
            structure_type=StructureType.HEAT_SLUG,
            origin=Point3D(
                x=-parameters.heat_slug.length / 2,
                y=-parameters.heat_slug.width / 2,
                z=current_z,
            ),
            size=Size3D(
                x=parameters.heat_slug.length,
                y=parameters.heat_slug.width,
                z=parameters.heat_slug.thickness,
            ),
            material_id=parameters.heat_slug.material.id,
            parent_group_id=group_id,
        )
        blocks.append(slug)
        materials.append(parameters.heat_slug.material)
        current_z = slug.max_z
        current_length = parameters.heat_slug.length
        current_width = parameters.heat_slug.width
        top_surface_block_ids = [slug.id]

    if parameters.lid.enabled:
        interface = _interface_block(
            block_id="top-to-lid-interface",
            name="Top structure to lid interface",
            length=current_length,
            width=current_width,
            thickness=parameters.lid.interface_thickness,
            base_z=current_z,
            material=parameters.lid.interface_material,
            group_id=group_id,
        )
        blocks.append(interface)
        materials.append(parameters.lid.interface_material)
        current_z = interface.max_z
        lid = AxisAlignedBlock(
            id="lid",
            name="Package lid",
            structure_type=StructureType.LID,
            origin=Point3D(
                x=-parameters.lid.length / 2,
                y=-parameters.lid.width / 2,
                z=current_z,
            ),
            size=Size3D(
                x=parameters.lid.length,
                y=parameters.lid.width,
                z=parameters.lid.thickness,
            ),
            material_id=parameters.lid.material.id,
            parent_group_id=group_id,
        )
        blocks.append(lid)
        materials.append(parameters.lid.material)
        top_surface_block_ids = [lid.id]

    return BuiltTopStack(
        blocks=blocks,
        materials=materials,
        top_surface_block_ids=top_surface_block_ids,
    )


def _interface_block(
    block_id: str,
    name: str,
    length: float,
    width: float,
    thickness: float,
    base_z: float,
    material: Material,
    group_id: str,
) -> AxisAlignedBlock:
    return AxisAlignedBlock(
        id=block_id,
        name=name,
        structure_type=StructureType.THERMAL_INTERFACE,
        origin=Point3D(x=-length / 2, y=-width / 2, z=base_z),
        size=Size3D(x=length, y=width, z=thickness),
        material_id=material.id,
        parent_group_id=group_id,
    )
