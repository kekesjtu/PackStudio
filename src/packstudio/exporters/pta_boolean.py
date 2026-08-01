from collections import defaultdict
from dataclasses import dataclass

from packstudio.domain.enums import StructureType
from packstudio.domain.geometry import (
    BOOLEAN_SOURCE_ID_KEY,
    BOOLEAN_SOURCE_NAME_KEY,
    AxisAlignedBlock,
    RectangleOperation,
    RectangularBooleanBlock,
)


@dataclass(frozen=True)
class CompactedBooleanBlock:
    geometry: RectangularBooleanBlock
    volumetric_heat_source: float


def compact_boolean_blocks(
    blocks: list[AxisAlignedBlock],
    source_density: dict[str, float],
) -> list[CompactedBooleanBlock]:
    """Compact coplanar cuboids into exact extruded XY boolean profiles.

    Z position and thickness are part of the compatibility key.  PTA layer planning
    decides where a physical block must be sliced before calling this function, so
    this compressor never creates an extrusion that violates layer Z semantics.
    """
    grouped: dict[
        tuple[str, str, StructureType, str, str, float, float, float],
        list[AxisAlignedBlock],
    ] = defaultdict(list)
    for block in blocks:
        source_id = str(block.metadata.get(BOOLEAN_SOURCE_ID_KEY, block.id))
        source_name = str(block.metadata.get(BOOLEAN_SOURCE_NAME_KEY, block.name))
        density = _snap(source_density.get(block.id, 0))
        key = (
            source_id,
            source_name,
            block.structure_type,
            block.material_id,
            block.parent_group_id,
            density,
            _snap(block.origin.z),
            _snap(block.size.z),
        )
        grouped[key].append(block)

    compacted: list[CompactedBooleanBlock] = []
    for solid_index, (key, source_blocks) in enumerate(grouped.items(), start=1):
        (
            source_id,
            source_name,
            structure_type,
            material_id,
            group_id,
            density,
            z,
            thickness,
        ) = key
        compacted.append(
            CompactedBooleanBlock(
                geometry=RectangularBooleanBlock(
                    id=f"{source_id}-boolean-{solid_index}",
                    name=source_name,
                    structure_type=structure_type,
                    z=z,
                    thickness=thickness,
                    material_id=material_id,
                    parent_group_id=group_id,
                    operations=_compact_xy(source_blocks),
                    source_block_ids=sorted(block.id for block in source_blocks),
                ),
                volumetric_heat_source=density,
            )
        )
    return compacted


def _compact_xy(blocks: list[AxisAlignedBlock]) -> list[RectangleOperation]:
    xs = sorted({_snap(value) for block in blocks for value in (block.origin.x, block.max_x)})
    ys = sorted({_snap(value) for block in blocks for value in (block.origin.y, block.max_y)})
    x_index = {value: index for index, value in enumerate(xs)}
    y_index = {value: index for index, value in enumerate(ys)}
    difference = [[0 for _ in ys] for _ in xs]

    for block in blocks:
        x0 = x_index[_snap(block.origin.x)]
        x1 = x_index[_snap(block.max_x)]
        y0 = y_index[_snap(block.origin.y)]
        y1 = y_index[_snap(block.max_y)]
        difference[x0][y0] += 1
        difference[x1][y0] -= 1
        difference[x0][y1] -= 1
        difference[x1][y1] += 1

    occupied = [[False for _ in range(len(ys) - 1)] for _ in range(len(xs) - 1)]
    for x in range(len(xs) - 1):
        for y in range(len(ys) - 1):
            value = difference[x][y]
            if x:
                value += difference[x - 1][y]
            if y:
                value += difference[x][y - 1]
            if x and y:
                value -= difference[x - 1][y - 1]
            difference[x][y] = value
            occupied[x][y] = value > 0

    additive = _rectangles_from_mask(occupied, xs, ys, target=True)
    missing = _rectangles_from_mask(occupied, xs, ys, target=False)
    if len(missing) + 1 < len(additive):
        return [
            RectangleOperation(
                add=True,
                x=xs[0],
                y=ys[0],
                width=xs[-1] - xs[0],
                height=ys[-1] - ys[0],
            ),
            *[RectangleOperation(add=False, **rectangle) for rectangle in missing],
        ]
    return [RectangleOperation(add=True, **rectangle) for rectangle in additive]


def _rectangles_from_mask(
    mask: list[list[bool]],
    xs: list[float],
    ys: list[float],
    *,
    target: bool,
) -> list[dict[str, float]]:
    rectangles: list[dict[str, float]] = []
    active: dict[tuple[int, int], int] = {}
    for y in range(len(ys) - 1):
        runs = _row_runs(mask, y, target)
        current = set(runs)
        for run, start_y in list(active.items()):
            if run not in current:
                rectangles.append(_rectangle(run, start_y, y, xs, ys))
                del active[run]
        for run in runs:
            active.setdefault(run, y)
    for run, start_y in active.items():
        rectangles.append(_rectangle(run, start_y, len(ys) - 1, xs, ys))
    return rectangles


def _row_runs(
    mask: list[list[bool]],
    y: int,
    target: bool,
) -> list[tuple[int, int]]:
    runs = []
    start: int | None = None
    for x in range(len(mask)):
        if mask[x][y] == target and start is None:
            start = x
        if mask[x][y] != target and start is not None:
            runs.append((start, x))
            start = None
    if start is not None:
        runs.append((start, len(mask)))
    return runs


def _rectangle(
    run: tuple[int, int],
    start_y: int,
    end_y: int,
    xs: list[float],
    ys: list[float],
) -> dict[str, float]:
    return {
        "x": xs[run[0]],
        "y": ys[start_y],
        "width": xs[run[1]] - xs[run[0]],
        "height": ys[end_y] - ys[start_y],
    }


def _snap(value: float) -> float:
    return float(f"{value:.12g}")
