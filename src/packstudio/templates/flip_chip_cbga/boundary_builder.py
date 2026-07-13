from packstudio.domain.enums import BlockFace, BoundaryKind, StructureType
from packstudio.domain.geometry import AxisAlignedBlock
from packstudio.domain.thermal import BoundaryCondition, SurfaceReference
from packstudio.templates.flip_chip_cbga.layer_builder import BuiltArrayLayer
from packstudio.templates.flip_chip_cbga.parameters import FlipChipCbgaParameters


def build_thermal_boundaries(
    parameters: FlipChipCbgaParameters,
    ball_layer: BuiltArrayLayer,
    blocks: list[AxisAlignedBlock],
    top_surface_block_ids: list[str],
) -> list[BoundaryCondition]:
    block_by_id = {block.id: block for block in blocks}
    bottom_blocks = [
        block
        for block in ball_layer.blocks
        if block.structure_type is StructureType.SOLDER_BALL
        and abs(block.origin.z + parameters.solder_balls.height) <= 1e-9
    ]
    board_coefficient = _coefficient_for_total_resistance(
        parameters.environment.board_to_ambient_thermal_resistance_k_w,
        bottom_blocks,
    )
    top_blocks = [block_by_id[block_id] for block_id in top_surface_block_ids]
    top_resistance = parameters.environment.top_to_ambient_thermal_resistance_k_w
    top_coefficient = (
        parameters.environment.default_convection_coefficient_w_m2k
        if top_resistance is None
        else _coefficient_for_total_resistance(top_resistance, top_blocks)
    )
    ambient = parameters.environment.ambient_temperature_k
    return [
        BoundaryCondition(
            id="pcb-side-cooling",
            name="PCB-side equivalent cooling",
            kind=BoundaryKind.CONVECTION,
            targets=[
                SurfaceReference(block_id=block.id, face=BlockFace.Z_MIN) for block in bottom_blocks
            ],
            convection_coefficient_w_m2k=board_coefficient,
            ambient_temperature_k=ambient,
        ),
        BoundaryCondition(
            id="top-surface-cooling",
            name="Top surface cooling",
            kind=BoundaryKind.CONVECTION,
            targets=[
                SurfaceReference(block_id=block.id, face=BlockFace.Z_MAX) for block in top_blocks
            ],
            convection_coefficient_w_m2k=top_coefficient,
            ambient_temperature_k=ambient,
        ),
    ]


def _coefficient_for_total_resistance(
    resistance_k_w: float,
    blocks: list[AxisAlignedBlock],
) -> float:
    area_m2 = sum(block.size.x * block.size.y for block in blocks) * 1e-6
    if area_m2 <= 0:
        raise ValueError("thermal resistance boundary requires a positive target area")
    return 1 / (resistance_k_w * area_m2)
