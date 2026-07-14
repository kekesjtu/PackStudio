from packstudio.domain.enums import StructureType
from packstudio.domain.geometry import AxisAlignedBlock, Point3D, Size3D
from packstudio.domain.materials import Material
from packstudio.domain.model import ModelGroup, PackageModel
from packstudio.domain.thermal import HeatSource
from packstudio.templates.flip_chip_cbga.boundary_builder import build_thermal_boundaries
from packstudio.templates.flip_chip_cbga.encapsulant_builder import build_encapsulant
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
        "encapsulant": [],
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

    has_top_structure = parameters.heat_slug.enabled or parameters.lid.enabled
    encapsulant_blocks = build_encapsulant(
        parameters,
        substrate.max_z,
        "encapsulant",
        cover_die=not has_top_structure,
    )
    blocks.extend(encapsulant_blocks)
    group_blocks["encapsulant"].extend(block.id for block in encapsulant_blocks)
    if encapsulant_blocks:
        _register_material(materials, parameters.encapsulant.material)

    ball_layer = build_array_layer(
        parameters=parameters.solder_balls,
        base_z=-parameters.solder_balls.height,
        prefix="solder-ball",
        element_structure=StructureType.SOLDER_BALL,
        matrix_structure=StructureType.STATIC_AIR,
        group_ids={
            "default": "solder-ball",
            "array": "solder-ball",
            "perimeter": "solder-ball",
            "center": "center-sball",
            "void": "solder-ball",
        },
    )
    _append_layer(blocks, group_blocks, materials, ball_layer, parameters.solder_balls)

    top_stack = build_top_stack(
        parameters,
        die.max_z,
        parameters.die.length,
        parameters.die.width,
        "top",
    )
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
    top_surface_block_ids = top_stack.top_surface_block_ids
    if not top_surface_block_ids:
        top_surface_block_ids = ["encapsulant-cap"] if encapsulant_blocks else [die.id]
    boundaries = build_thermal_boundaries(
        parameters,
        ball_layer,
        blocks,
        top_surface_block_ids,
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
            "flip_chip_bump_cell_density_per_mm2": 1
            / (parameters.flip_chip_bumps.pitch_x * parameters.flip_chip_bumps.pitch_y),
            "flip_chip_bump_fill_fraction": bump_layer.blocks[0].metadata["fill_fraction"],
            "solder_ball_equivalent_regions": ball_layer.equivalent_region_count,
            "encapsulant_block_count": len(encapsulant_blocks),
            "mesh_resolution": parameters.mesh.resolution.value,
            "ambient_temperature_k": parameters.environment.ambient_temperature_k,
            "default_convection_coefficient_w_m2k": (
                parameters.environment.default_convection_coefficient_w_m2k
            ),
            "pcb_convection_coefficient_w_m2k": (
                parameters.environment.pcb_convection_coefficient_w_m2k
            ),
            "top_convection_coefficient_w_m2k": (
                parameters.environment.top_convection_coefficient_w_m2k
            ),
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
        "encapsulant": "Encapsulant",
        "fc-bumps": "fc_bumps",
        "solder-ball": "Solder_ball",
        "center-sball": "Center_SBall",
        "top": "Top structures",
    }
    for group_id, label in labels.items():
        optional_groups = {"center-sball", "encapsulant", "top"}
        if group_id in optional_groups and not group_blocks[group_id]:
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
