from packstudio.domain.enums import StructureType
from packstudio.domain.geometry import AxisAlignedBlock, Point3D, Size3D
from packstudio.templates.flip_chip_cbga.parameters import FlipChipCbgaParameters


def build_encapsulant(
    parameters: FlipChipCbgaParameters,
    substrate_top_z: float,
    group_id: str,
) -> list[AxisAlignedBlock]:
    """Build two cavity rings plus a cap that submerges the die."""
    if not parameters.encapsulant.enabled:
        return []

    lower_ring = _ring_blocks(
        parameters=parameters,
        tier="lower",
        base_z=substrate_top_z,
        height=parameters.flip_chip_bumps.height,
        group_id=group_id,
    )
    upper_ring = _ring_blocks(
        parameters=parameters,
        tier="upper",
        base_z=substrate_top_z + parameters.flip_chip_bumps.height,
        height=parameters.die.thickness,
        group_id=group_id,
    )
    cap = AxisAlignedBlock(
        id="encapsulant-cap",
        name="Encapsulant top cover",
        structure_type=StructureType.ENCAPSULANT,
        origin=Point3D(
            x=-parameters.encapsulant.length / 2,
            y=-parameters.encapsulant.width / 2,
            z=substrate_top_z + parameters.flip_chip_bumps.height + parameters.die.thickness,
        ),
        size=Size3D(
            x=parameters.encapsulant.length,
            y=parameters.encapsulant.width,
            z=parameters.encapsulant.cover_thickness,
        ),
        material_id=parameters.encapsulant.material.id,
        parent_group_id=group_id,
        metadata={"tier": "cap"},
    )
    return [*lower_ring, *upper_ring, cap]


def _ring_blocks(
    parameters: FlipChipCbgaParameters,
    tier: str,
    base_z: float,
    height: float,
    group_id: str,
) -> list[AxisAlignedBlock]:
    encapsulant = parameters.encapsulant
    die = parameters.die
    outer_x = -encapsulant.length / 2
    outer_y = -encapsulant.width / 2
    die_x = -die.length / 2
    die_y = -die.width / 2
    side_width = (encapsulant.length - die.length) / 2
    side_depth = (encapsulant.width - die.width) / 2
    parts = [
        ("front", outer_x, outer_y, encapsulant.length, side_depth),
        (
            "back",
            outer_x,
            die_y + die.width,
            encapsulant.length,
            side_depth,
        ),
        ("left", outer_x, die_y, side_width, die.width),
        ("right", die_x + die.length, die_y, side_width, die.width),
    ]
    return [
        AxisAlignedBlock(
            id=f"encapsulant-{tier}-{name}",
            name=f"Encapsulant {tier} {name}",
            structure_type=StructureType.ENCAPSULANT,
            origin=Point3D(x=origin_x, y=origin_y, z=base_z),
            size=Size3D(x=size_x, y=size_y, z=height),
            material_id=encapsulant.material.id,
            parent_group_id=group_id,
            metadata={"tier": tier, "side": name},
        )
        for name, origin_x, origin_y, size_x, size_y in parts
    ]
