from dataclasses import dataclass

from packstudio.templates.flip_chip_cbga.parameters import (
    ArrayLayerParameters,
    ArrayPattern,
)


@dataclass(frozen=True)
class ArrayCell:
    row: int
    column: int
    center_x: float
    center_y: float
    present: bool
    group: str


@dataclass(frozen=True)
class CellRegion:
    row_start: int
    row_end: int
    column_start: int
    column_end: int
    group: str
    x_shift: float = 0

    @property
    def row_count(self) -> int:
        return self.row_end - self.row_start

    @property
    def column_count(self) -> int:
        return self.column_end - self.column_start


def build_array_cells(parameters: ArrayLayerParameters) -> list[ArrayCell]:
    omitted = {(cell.row, cell.column) for cell in parameters.omitted_cells}
    center_bounds = _center_bounds(parameters)
    cells: list[ArrayCell] = []

    for row in range(parameters.rows):
        center_y = (row - (parameters.rows - 1) / 2) * parameters.pitch_y
        row_shift = _staggered_row_shift(parameters, row)
        for column in range(parameters.columns):
            center_x = (column - (parameters.columns - 1) / 2) * parameters.pitch_x + row_shift
            in_center = _is_in_center(row, column, center_bounds)
            present, group = _cell_state(parameters, row, column, in_center, omitted)
            cells.append(
                ArrayCell(
                    row=row,
                    column=column,
                    center_x=center_x,
                    center_y=center_y,
                    present=present,
                    group=group,
                )
            )
    return cells


def occupied_regions(parameters: ArrayLayerParameters) -> list[CellRegion]:
    if parameters.pattern is ArrayPattern.STAGGERED:
        return [
            CellRegion(
                row_start=row,
                row_end=row + 1,
                column_start=0,
                column_end=parameters.columns,
                group="array",
                x_shift=_staggered_row_shift(parameters, row),
            )
            for row in range(parameters.rows)
        ]

    cells = build_array_cells(parameters)
    groups = sorted({cell.group for cell in cells if cell.present})
    regions: list[CellRegion] = []
    for group in groups:
        mask = [
            [
                _cell_at(cells, parameters.columns, row, column).present
                and _cell_at(cells, parameters.columns, row, column).group == group
                for column in range(parameters.columns)
            ]
            for row in range(parameters.rows)
        ]
        regions.extend(_partition_mask(mask, group))
    return regions


def unoccupied_regions(parameters: ArrayLayerParameters) -> list[CellRegion]:
    if parameters.pattern is ArrayPattern.STAGGERED:
        return []
    cells = build_array_cells(parameters)
    mask = [
        [
            not _cell_at(cells, parameters.columns, row, column).present
            for column in range(parameters.columns)
        ]
        for row in range(parameters.rows)
    ]
    return _partition_mask(mask, "void")


def region_geometry(
    parameters: ArrayLayerParameters, region: CellRegion
) -> tuple[float, float, float, float]:
    origin_x = (
        -parameters.columns * parameters.pitch_x / 2
        + region.column_start * parameters.pitch_x
        + region.x_shift
    )
    origin_y = -parameters.rows * parameters.pitch_y / 2 + (region.row_start * parameters.pitch_y)
    return (
        origin_x,
        origin_y,
        region.column_count * parameters.pitch_x,
        region.row_count * parameters.pitch_y,
    )


def _cell_state(
    parameters: ArrayLayerParameters,
    row: int,
    column: int,
    in_center: bool,
    omitted: set[tuple[int, int]],
) -> tuple[bool, str]:
    if parameters.pattern is ArrayPattern.CENTER_DEPOPULATED:
        return (not in_center, "void" if in_center else "perimeter")
    if parameters.pattern is ArrayPattern.CENTER_POPULATED:
        return (True, "center" if in_center else "perimeter")
    if parameters.pattern is ArrayPattern.CUSTOM and (row, column) in omitted:
        return (False, "void")
    return (True, "array")


def _center_bounds(parameters: ArrayLayerParameters) -> tuple[int, int, int, int] | None:
    center_patterns = {ArrayPattern.CENTER_DEPOPULATED, ArrayPattern.CENTER_POPULATED}
    if parameters.pattern not in center_patterns:
        return None
    row_start = (parameters.rows - parameters.center_rows) // 2
    column_start = (parameters.columns - parameters.center_columns) // 2
    return (
        row_start,
        row_start + parameters.center_rows,
        column_start,
        column_start + parameters.center_columns,
    )


def _is_in_center(row: int, column: int, bounds: tuple[int, int, int, int] | None) -> bool:
    if bounds is None:
        return False
    row_start, row_end, column_start, column_end = bounds
    return row_start <= row < row_end and column_start <= column < column_end


def _staggered_row_shift(parameters: ArrayLayerParameters, row: int) -> float:
    if parameters.pattern is not ArrayPattern.STAGGERED:
        return 0
    return (-0.25 if row % 2 == 0 else 0.25) * parameters.pitch_x


def _cell_at(cells: list[ArrayCell], columns: int, row: int, column: int) -> ArrayCell:
    return cells[row * columns + column]


def _partition_mask(mask: list[list[bool]], group: str) -> list[CellRegion]:
    if not mask or not mask[0]:
        return []
    rows, columns = len(mask), len(mask[0])
    visited = [[False] * columns for _ in range(rows)]
    regions: list[CellRegion] = []

    for row in range(rows):
        for column in range(columns):
            if not mask[row][column] or visited[row][column]:
                continue
            column_end = column
            while column_end < columns and mask[row][column_end] and not visited[row][column_end]:
                column_end += 1

            row_end = row + 1
            while row_end < rows and all(
                mask[row_end][candidate] and not visited[row_end][candidate]
                for candidate in range(column, column_end)
            ):
                row_end += 1

            for visited_row in range(row, row_end):
                for visited_column in range(column, column_end):
                    visited[visited_row][visited_column] = True
            regions.append(
                CellRegion(
                    row_start=row,
                    row_end=row_end,
                    column_start=column,
                    column_end=column_end,
                    group=group,
                )
            )
    return regions
