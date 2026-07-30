from collections import defaultdict
from dataclasses import dataclass, field
from math import isclose

from packstudio.domain.enums import BlockFace, BoundaryKind, StructureType
from packstudio.domain.geometry import AxisAlignedBlock
from packstudio.domain.materials import Material
from packstudio.domain.model import ModelGroup, PackageModel
from packstudio.domain.thermal import BoundaryCondition, HeatSource, SurfaceReference
from packstudio.templates.package_library.core.definitions import TemplateDefinition
from packstudio.templates.package_library.core.geometry import DraftBlock, normalize_drafts
from packstudio.templates.package_library.core.materials import production_materials
from packstudio.templates.package_library.core.parameters import TemplateRequest


@dataclass
class BuiltTemplate:
    drafts: list[DraftBlock] = field(default_factory=list)
    blocks: list[AxisAlignedBlock] = field(default_factory=list)
    materials: list[Material] = field(default_factory=list)
    group_names: dict[str, str] = field(default_factory=dict)
    power_w: float = 0
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)


def generate_template(
    definition: TemplateDefinition,
    request: TemplateRequest,
) -> PackageModel:
    values = definition.validate_request(request)
    built: BuiltTemplate = definition.builder(values, request)
    normalized = normalize_drafts(built.drafts)
    blocks = [*normalized.blocks, *built.blocks]
    group_names = {**normalized.group_names, **built.group_names}
    materials = {**production_materials()}
    materials.update((item.id, item) for item in built.materials)
    materials.update((item.id, item) for item in request.custom_materials)
    blocks = _apply_material_assignments(blocks, materials, request)
    groups = _build_groups(blocks, group_names, definition.display_name)
    power = request.die_power_w if request.die_power_w is not None else built.power_w
    heat_sources = _build_heat_sources(blocks, power)
    boundaries = _build_boundaries(blocks, request)
    used_ids = {block.material_id for block in blocks}
    return PackageModel(
        template_id=definition.id.replace("_", "-"),
        name=request.design_name or definition.display_name,
        materials=[materials[identifier] for identifier in sorted(used_ids)],
        blocks=blocks,
        groups=groups,
        heat_sources=heat_sources,
        boundaries=boundaries,
        metadata={
            "implementation": "packstudio-native",
            "template_version": "2.1",
            "reference_basis": "handwritten transcription of reviewed FloTHERM PACK 2504 data",
            "reference_geometry_status": "baseline-and-mapped-single-variable-transcription",
            "runtime_reference_data_required": False,
            "mesh_resolution": request.mesh.resolution.value,
            "ambient_temperature_k": request.environment.ambient_temperature_k,
            "default_convection_coefficient_w_m2k": (
                request.environment.default_convection_coefficient_w_m2k
            ),
            "pcb_convection_coefficient_w_m2k": (
                request.environment.pcb_convection_coefficient_w_m2k
            ),
            "top_convection_coefficient_w_m2k": (
                request.environment.top_convection_coefficient_w_m2k
            ),
            "mesh_data_included": False,
            "solver_results_included": False,
            **built.metadata,
        },
    )


def _apply_material_assignments(
    blocks: list[AxisAlignedBlock],
    materials: dict[str, Material],
    request: TemplateRequest,
) -> list[AxisAlignedBlock]:
    missing = sorted(set(request.material_assignments.values()) - set(materials))
    if missing:
        raise ValueError(f"unknown material assignments: {missing}")
    return [
        block.model_copy(
            update={
                "material_id": request.material_assignments.get(
                    block.id,
                    request.material_assignments.get(
                        block.parent_group_id,
                        block.material_id,
                    ),
                )
            }
        )
        for block in blocks
    ]


def _build_groups(
    blocks: list[AxisAlignedBlock],
    names: dict[str, str],
    package_name: str,
) -> list[ModelGroup]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for block in blocks:
        grouped[block.parent_group_id].append(block.id)
    groups = [ModelGroup(id="package", name=package_name)]
    for group_id, block_ids in grouped.items():
        parent_id = "group-solder-ball" if group_id == "group-center-solder-ball" else "package"
        groups.append(
            ModelGroup(
                id=group_id,
                name=names.get(group_id, group_id),
                parent_id=parent_id,
                block_ids=block_ids,
            )
        )
    return groups


def _build_heat_sources(blocks: list[AxisAlignedBlock], power_w: float) -> list[HeatSource]:
    dies = [block for block in blocks if block.structure_type is StructureType.DIE]
    if not dies:
        raise ValueError("production template must contain a die")
    total_volume = sum(block.size.x * block.size.y * block.size.z for block in dies)
    return [
        HeatSource(
            id=f"die-source-{index}",
            name=f"Die heat source {index}",
            block_id=block.id,
            power_w=power_w * block.size.x * block.size.y * block.size.z / total_volume,
        )
        for index, block in enumerate(dies, start=1)
    ]


def _build_boundaries(
    blocks: list[AxisAlignedBlock],
    request: TemplateRequest,
) -> list[BoundaryCondition]:
    minimum_z = min(block.origin.z for block in blocks)
    maximum_z = max(block.max_z for block in blocks)
    bottom = [block for block in blocks if isclose(block.origin.z, minimum_z, abs_tol=1e-9)]
    top = [block for block in blocks if isclose(block.max_z, maximum_z, abs_tol=1e-9)]
    environment = request.environment
    return [
        BoundaryCondition(
            id="pcb-side-cooling",
            name="PCB-side equivalent cooling",
            kind=BoundaryKind.CONVECTION,
            targets=[SurfaceReference(block_id=block.id, face=BlockFace.Z_MIN) for block in bottom],
            convection_coefficient_w_m2k=(environment.pcb_convection_coefficient_w_m2k),
            ambient_temperature_k=environment.ambient_temperature_k,
        ),
        BoundaryCondition(
            id="top-surface-cooling",
            name="Top surface cooling",
            kind=BoundaryKind.CONVECTION,
            targets=[SurfaceReference(block_id=block.id, face=BlockFace.Z_MAX) for block in top],
            convection_coefficient_w_m2k=(environment.top_convection_coefficient_w_m2k),
            ambient_temperature_k=environment.ambient_temperature_k,
        ),
    ]
