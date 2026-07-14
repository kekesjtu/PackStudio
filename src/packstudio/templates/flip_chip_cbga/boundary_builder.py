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
    top_blocks = [block_by_id[block_id] for block_id in top_surface_block_ids]
    ambient = parameters.environment.ambient_temperature_k
    return [
        BoundaryCondition(
            id="pcb-side-cooling",
            name="PCB-side equivalent cooling",
            kind=BoundaryKind.CONVECTION,
            targets=[
                SurfaceReference(block_id=block.id, face=BlockFace.Z_MIN) for block in bottom_blocks
            ],
            convection_coefficient_w_m2k=(parameters.environment.pcb_convection_coefficient_w_m2k),
            ambient_temperature_k=ambient,
        ),
        BoundaryCondition(
            id="top-surface-cooling",
            name="Top surface cooling",
            kind=BoundaryKind.CONVECTION,
            targets=[
                SurfaceReference(block_id=block.id, face=BlockFace.Z_MAX) for block in top_blocks
            ],
            convection_coefficient_w_m2k=(parameters.environment.top_convection_coefficient_w_m2k),
            ambient_temperature_k=ambient,
        ),
    ]
