from packstudio.domain.enums import BlockFace, BoundaryKind, StructureType
from packstudio.domain.geometry import AxisAlignedBlock, Point3D, Size3D
from packstudio.domain.materials import Material
from packstudio.domain.model import ModelGroup, PackageModel
from packstudio.domain.thermal import BoundaryCondition, HeatSource, SurfaceReference
from packstudio.templates.flip_chip_cbga.layer_builder import (
    BuiltArrayLayer,
    build_array_layer,
)
from packstudio.templates.flip_chip_cbga.parameters import (
    ArrayLayerParameters,
    FlipChipCbgaParameters,
)
from packstudio.templates.flip_chip_cbga.top_builder import build_top_stack


def generate_flip_chip_cbga(parameters: FlipChipCbgaParameters) -> PackageModel:
    materials: dict[str, Material] = {}
    blocks: list[AxisAlignedBlock] = []
    group_blocks: dict[str, list[str]] = {
        "substrate": [],
        "die": [],
        "fc-bumps": [],
        "solder-ball": [],
        "center-sball": [],
        "top": [],
    }

    substrate = AxisAlignedBlock(
        id="substrate",
        name="Package substrate",
        structure_type=StructureType.SUBSTRATE,
        origin=Point3D(
            x=-parameters.substrate.length / 2,
            y=-parameters.substrate.width / 2,
            z=0,
        ),
        size=Size3D(
            x=parameters.substrate.length,
            y=parameters.substrate.width,
            z=parameters.substrate.thickness,
        ),
        material_id=parameters.substrate.material.id,
        parent_group_id="substrate",
    )
    blocks.append(substrate)
    group_blocks["substrate"].append(substrate.id)
    _register_material(materials, parameters.substrate.material)

    bump_layer = build_array_layer(
        parameters=parameters.flip_chip_bumps,
        base_z=substrate.max_z,
        prefix="fc-bump",
        element_structure=StructureType.FLIP_CHIP_BUMP,
        matrix_structure=StructureType.UNDERFILL,
        group_ids={"default": "fc-bumps"},
    )
    _append_layer(blocks, group_blocks, materials, bump_layer, parameters.flip_chip_bumps)

    die = AxisAlignedBlock(
        id="die",
        name="Silicon die",
        structure_type=StructureType.DIE,
        origin=Point3D(
            x=-parameters.die.length / 2,
            y=-parameters.die.width / 2,
            z=substrate.max_z + parameters.flip_chip_bumps.height,
        ),
        size=Size3D(
            x=parameters.die.length,
            y=parameters.die.width,
            z=parameters.die.thickness,
        ),
        material_id=parameters.die.material.id,
        parent_group_id="die",
    )
    blocks.append(die)
    group_blocks["die"].append(die.id)
    _register_material(materials, parameters.die.material)

    ball_layer = build_array_layer(
        parameters=parameters.solder_balls,
        base_z=-parameters.solder_balls.height,
        prefix="solder-ball",
        element_structure=StructureType.SOLDER_BALL,
        matrix_structure=StructureType.SOLDER_BALL_MATRIX,
        group_ids={
            "default": "solder-ball",
            "array": "solder-ball",
            "perimeter": "solder-ball",
            "center": "center-sball",
            "void": "solder-ball",
        },
    )
    _append_layer(blocks, group_blocks, materials, ball_layer, parameters.solder_balls)

    top_stack = build_top_stack(parameters, die.max_z, "top")
    blocks.extend(top_stack.blocks)
    group_blocks["top"].extend(block.id for block in top_stack.blocks)
    for material in top_stack.materials:
        _register_material(materials, material)

    heat_sources = [
        HeatSource(
            id="die-source",
            name="Die uniform heat source",
            block_id=die.id,
            power_w=parameters.die.power_w,
        )
    ]
    boundaries = _build_boundaries(
        parameters,
        ball_layer,
        top_stack.top_surface_block_ids,
    )
    groups = _build_groups(group_blocks)

    return PackageModel(
        template_id="flip-chip-cbga",
        name=parameters.design_name,
        materials=list(materials.values()),
        blocks=blocks,
        groups=groups,
        heat_sources=heat_sources,
        boundaries=boundaries,
        metadata={
            "flip_chip_bump_count": bump_layer.physical_element_count,
            "solder_ball_count": ball_layer.physical_element_count,
            "flip_chip_equivalent_regions": bump_layer.equivalent_region_count,
            "solder_ball_equivalent_regions": ball_layer.equivalent_region_count,
            "mesh_data_included": False,
            "solver_results_included": False,
        },
    )


def _append_layer(
    blocks: list[AxisAlignedBlock],
    group_blocks: dict[str, list[str]],
    materials: dict[str, Material],
    layer: BuiltArrayLayer,
    parameters: ArrayLayerParameters,
) -> None:
    blocks.extend(layer.blocks)
    for group_id, block_ids in layer.block_ids_by_group.items():
        group_blocks[group_id].extend(block_ids)
    for material in (
        parameters.element_material,
        parameters.matrix_material,
        *layer.generated_materials,
    ):
        _register_material(materials, material)


def _register_material(materials: dict[str, Material], material: Material) -> None:
    existing = materials.get(material.id)
    if existing is not None and existing != material:
        raise ValueError(f"material id {material.id} has conflicting definitions")
    materials[material.id] = material


def _build_groups(group_blocks: dict[str, list[str]]) -> list[ModelGroup]:
    groups = [ModelGroup(id="package", name="Flip Chip CBGA")]
    labels = {
        "substrate": "Substrate",
        "die": "Die",
        "fc-bumps": "fc_bumps",
        "solder-ball": "Solder_ball",
        "center-sball": "Center_SBall",
        "top": "Top structures",
    }
    for group_id, label in labels.items():
        if group_id == "center-sball" and not group_blocks[group_id]:
            continue
        parent_id = "solder-ball" if group_id == "center-sball" else "package"
        groups.append(
            ModelGroup(
                id=group_id,
                name=label,
                parent_id=parent_id,
                block_ids=group_blocks[group_id],
            )
        )
    return groups


def _build_boundaries(
    parameters: FlipChipCbgaParameters,
    ball_layer: BuiltArrayLayer,
    top_surface_block_ids: list[str],
) -> list[BoundaryCondition]:
    boundaries: list[BoundaryCondition] = []
    environment = parameters.environment
    if environment.bottom_convection_coefficient_w_m2k is not None:
        bottom_ids = [
            block.id
            for block in ball_layer.blocks
            if abs(block.origin.z + parameters.solder_balls.height) <= 1e-9
        ]
        boundaries.append(
            BoundaryCondition(
                id="bottom-convection",
                name="Bottom convection",
                kind=BoundaryKind.CONVECTION,
                targets=[
                    SurfaceReference(block_id=block_id, face=BlockFace.Z_MIN)
                    for block_id in bottom_ids
                ],
                convection_coefficient_w_m2k=(environment.bottom_convection_coefficient_w_m2k),
                ambient_temperature_k=environment.ambient_temperature_k,
            )
        )
    if environment.top_convection_coefficient_w_m2k is not None:
        boundaries.append(
            BoundaryCondition(
                id="top-convection",
                name="Top convection",
                kind=BoundaryKind.CONVECTION,
                targets=[
                    SurfaceReference(block_id=block_id, face=BlockFace.Z_MAX)
                    for block_id in top_surface_block_ids
                ],
                convection_coefficient_w_m2k=environment.top_convection_coefficient_w_m2k,
                ambient_temperature_k=environment.ambient_temperature_k,
            )
        )
    return boundaries
