from collections import defaultdict
from dataclasses import dataclass, field

from packstudio.domain.enums import StructureType
from packstudio.domain.geometry import AxisAlignedBlock
from packstudio.domain.materials import Material
from packstudio.domain.model import ModelGroup, PackageModel
from packstudio.domain.thermal import HeatSource
from packstudio.templates.package_library.core.definitions import TemplateDefinition
from packstudio.templates.package_library.core.geometry import DraftBlock, normalize_drafts
from packstudio.templates.package_library.core.materials import production_materials
from packstudio.templates.package_library.core.parameters import TemplateRequest
from packstudio.templates.package_library.core.preset_request import resolve_preset_request


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
    request, preset = resolve_preset_request(definition, request)
    values = definition.validate_request(request)
    built: BuiltTemplate = definition.builder(values, request)
    normalized = normalize_drafts(built.drafts)
    blocks = [*normalized.blocks, *built.blocks]
    group_names = {**normalized.group_names, **built.group_names}
    materials = {**production_materials()}
    materials.update((item.id, item) for item in built.materials)
    materials.update((item.id, item) for item in request.custom_materials)
    default_assignments = {
        item.group_id: item.default
        for item in definition.material_selections
        if values.matches(item.visible_when)
    }
    effective_request = request.model_copy(
        update={"material_assignments": {**default_assignments, **request.material_assignments}}
    )
    blocks = _apply_material_assignments(blocks, materials, effective_request)
    groups = _build_groups(blocks, group_names, definition.display_name)
    power = request.die_power_w if request.die_power_w is not None else built.power_w
    heat_sources = _build_heat_sources(blocks, power)
    used_ids = {block.material_id for block in blocks}
    footprint = next(
        (values.text(field.key) for field in definition.fields if field.control == "footprint"),
        None,
    )
    return PackageModel(
        template_id=definition.id.replace("_", "-"),
        name=request.design_name or definition.display_name,
        materials=[materials[identifier] for identifier in sorted(used_ids)],
        blocks=blocks,
        groups=groups,
        heat_sources=heat_sources,
        boundaries=[],
        metadata={
            "implementation": "packstudio-native",
            "template_version": "2.1",
            "reference_basis": "versioned JSON defaults with reviewed FloTHERM PACK 2504 mappings",
            "default_parameter_schema": "packstudio.default-parameters/v1",
            "reference_geometry_status": "baseline-and-mapped-single-variable-transcription",
            "runtime_reference_data_required": False,
            "outline_type": "standard_outline",
            "die_type": "actual_type",
            **({} if footprint is None else {"footprint_size": footprint}),
            "mesh_resolution": request.mesh.resolution.value,
            "mesh_data_included": False,
            "solver_results_included": False,
            **built.metadata,
            **({} if preset is None else preset.metadata),
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
