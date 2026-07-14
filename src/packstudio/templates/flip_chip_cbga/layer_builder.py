from dataclasses import dataclass

from packstudio.domain.enums import StructureType
from packstudio.domain.geometry import AxisAlignedBlock, Point3D, Size3D
from packstudio.domain.materials import Material
from packstudio.templates.flip_chip_cbga.equivalent import (
    calculate_cylindrical_array_equivalent,
    create_equivalent_material,
)
from packstudio.templates.flip_chip_cbga.layout import (
    ArrayCell,
    build_array_cells,
    occupied_regions,
    region_geometry,
    unoccupied_regions,
)
from packstudio.templates.flip_chip_cbga.parameters import (
    ArrayLayerParameters,
    ArrayRepresentation,
)


@dataclass(frozen=True)
class BuiltArrayLayer:
    blocks: list[AxisAlignedBlock]
    generated_materials: list[Material]
    block_ids_by_group: dict[str, list[str]]
    physical_element_count: int
    equivalent_region_count: int


def build_array_layer(
    parameters: ArrayLayerParameters,
    base_z: float,
    prefix: str,
    element_structure: StructureType,
    matrix_structure: StructureType,
    group_ids: dict[str, str],
) -> BuiltArrayLayer:
    if parameters.representation is ArrayRepresentation.EQUIVALENT:
        return _build_equivalent_layer(
            parameters,
            base_z,
            prefix,
            element_structure,
            matrix_structure,
            group_ids,
        )
    return _build_discrete_layer(
        parameters,
        base_z,
        prefix,
        element_structure,
        matrix_structure,
        group_ids,
    )


def _build_equivalent_layer(
    parameters: ArrayLayerParameters,
    base_z: float,
    prefix: str,
    element_structure: StructureType,
    matrix_structure: StructureType,
    group_ids: dict[str, str],
) -> BuiltArrayLayer:
    equivalent_material, properties = create_equivalent_material(
        material_id=f"{prefix}-equivalent",
        name=f"{prefix} element + matrix equivalent",
        element=parameters.element_material,
        matrix=parameters.matrix_material,
        radius=parameters.diameter / 2,
        pitch_x=parameters.pitch_x,
        pitch_y=parameters.pitch_y,
    )
    blocks: list[AxisAlignedBlock] = []
    block_ids_by_group: dict[str, list[str]] = {}
    regions = occupied_regions(parameters)

    for index, region in enumerate(regions, start=1):
        origin_x, origin_y, size_x, size_y = region_geometry(parameters, region)
        group_id = _resolve_group_id(group_ids, region.group)
        block = AxisAlignedBlock(
            id=f"{prefix}-{region.group}-equivalent-{index}",
            name=f"{prefix} {region.group} equivalent region {index}",
            structure_type=element_structure,
            origin=Point3D(x=origin_x, y=origin_y, z=base_z),
            size=Size3D(x=size_x, y=size_y, z=parameters.height),
            material_id=equivalent_material.id,
            parent_group_id=group_id,
            metadata={
                "representation": parameters.representation.value,
                "fill_fraction": properties.fill_fraction,
                "physical_elements": region.row_count * region.column_count,
            },
        )
        blocks.append(block)
        block_ids_by_group.setdefault(group_id, []).append(block.id)

    _append_void_region_blocks(
        blocks,
        block_ids_by_group,
        parameters,
        base_z,
        prefix,
        matrix_structure,
        group_ids,
    )
    physical_count = sum(cell.present for cell in build_array_cells(parameters))
    return BuiltArrayLayer(
        blocks=blocks,
        generated_materials=[equivalent_material],
        block_ids_by_group=block_ids_by_group,
        physical_element_count=physical_count,
        equivalent_region_count=len(regions),
    )


def _build_discrete_layer(
    parameters: ArrayLayerParameters,
    base_z: float,
    prefix: str,
    element_structure: StructureType,
    matrix_structure: StructureType,
    group_ids: dict[str, str],
) -> BuiltArrayLayer:
    properties = calculate_cylindrical_array_equivalent(
        element=parameters.element_material,
        matrix=parameters.matrix_material,
        radius=parameters.diameter / 2,
        pitch_x=parameters.pitch_x,
        pitch_y=parameters.pitch_y,
    )
    blocks: list[AxisAlignedBlock] = []
    block_ids_by_group: dict[str, list[str]] = {}
    cells = build_array_cells(parameters)

    for cell in cells:
        if not cell.present:
            continue
        group_id = _resolve_group_id(group_ids, cell.group)
        element_id = f"{prefix}-r{cell.row + 1}-c{cell.column + 1}"
        element = AxisAlignedBlock(
            id=element_id,
            name=f"{prefix} row {cell.row + 1} column {cell.column + 1}",
            structure_type=element_structure,
            origin=Point3D(
                x=cell.center_x - properties.replacement_side / 2,
                y=cell.center_y - properties.replacement_side / 2,
                z=base_z,
            ),
            size=Size3D(
                x=properties.replacement_side,
                y=properties.replacement_side,
                z=parameters.height,
            ),
            material_id=parameters.element_material.id,
            parent_group_id=group_id,
            metadata={
                "representation": parameters.representation.value,
                "row": cell.row,
                "column": cell.column,
                "source_shape": "equal-volume cylinder",
            },
        )
        blocks.append(element)
        block_ids_by_group.setdefault(group_id, []).append(element.id)
        _append_cell_matrix_blocks(
            blocks,
            block_ids_by_group,
            parameters,
            cell,
            properties.replacement_side,
            base_z,
            prefix,
            matrix_structure,
            group_id,
        )

    _append_void_region_blocks(
        blocks,
        block_ids_by_group,
        parameters,
        base_z,
        prefix,
        matrix_structure,
        group_ids,
    )
    return BuiltArrayLayer(
        blocks=blocks,
        generated_materials=[],
        block_ids_by_group=block_ids_by_group,
        physical_element_count=sum(cell.present for cell in cells),
        equivalent_region_count=0,
    )


def _append_cell_matrix_blocks(
    blocks: list[AxisAlignedBlock],
    block_ids_by_group: dict[str, list[str]],
    parameters: ArrayLayerParameters,
    cell: ArrayCell,
    element_side: float,
    base_z: float,
    prefix: str,
    matrix_structure: StructureType,
    group_id: str,
) -> None:
    half_gap_x = (parameters.pitch_x - element_side) / 2
    half_gap_y = (parameters.pitch_y - element_side) / 2
    cell_x = cell.center_x - parameters.pitch_x / 2
    cell_y = cell.center_y - parameters.pitch_y / 2
    parts = [
        ("left", cell_x, cell_y, half_gap_x, parameters.pitch_y),
        (
            "right",
            cell.center_x + element_side / 2,
            cell_y,
            half_gap_x,
            parameters.pitch_y,
        ),
        ("front", cell.center_x - element_side / 2, cell_y, element_side, half_gap_y),
        (
            "back",
            cell.center_x - element_side / 2,
            cell.center_y + element_side / 2,
            element_side,
            half_gap_y,
        ),
    ]
    for suffix, origin_x, origin_y, size_x, size_y in parts:
        if min(size_x, size_y) <= 1e-12:
            continue
        block_id = f"{prefix}-matrix-r{cell.row + 1}-c{cell.column + 1}-{suffix}"
        blocks.append(
            AxisAlignedBlock(
                id=block_id,
                name=f"{prefix} matrix {cell.row + 1},{cell.column + 1} {suffix}",
                structure_type=matrix_structure,
                origin=Point3D(x=origin_x, y=origin_y, z=base_z),
                size=Size3D(x=size_x, y=size_y, z=parameters.height),
                material_id=parameters.matrix_material.id,
                parent_group_id=group_id,
                metadata={"representation": "discrete-matrix"},
            )
        )
        block_ids_by_group.setdefault(group_id, []).append(block_id)


def _append_void_region_blocks(
    blocks: list[AxisAlignedBlock],
    block_ids_by_group: dict[str, list[str]],
    parameters: ArrayLayerParameters,
    base_z: float,
    prefix: str,
    matrix_structure: StructureType,
    group_ids: dict[str, str],
) -> None:
    group_id = _resolve_group_id(group_ids, "void")
    for index, region in enumerate(unoccupied_regions(parameters), start=1):
        origin_x, origin_y, size_x, size_y = region_geometry(parameters, region)
        block_id = f"{prefix}-void-matrix-{index}"
        blocks.append(
            AxisAlignedBlock(
                id=block_id,
                name=f"{prefix} void matrix region {index}",
                structure_type=matrix_structure,
                origin=Point3D(x=origin_x, y=origin_y, z=base_z),
                size=Size3D(x=size_x, y=size_y, z=parameters.height),
                material_id=parameters.matrix_material.id,
                parent_group_id=group_id,
                metadata={"representation": "uniform-matrix-fill"},
            )
        )
        block_ids_by_group.setdefault(group_id, []).append(block_id)


def _resolve_group_id(group_ids: dict[str, str], group: str) -> str:
    return group_ids.get(group, group_ids["default"])
