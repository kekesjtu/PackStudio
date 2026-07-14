from dataclasses import dataclass

from packstudio.templates.flip_chip_cbga.parameters import (
    ArrayLayerParameters,
    SolderBallParameters,
)
from packstudio.templates.flip_chip_cbga.solder_style import center_bounds, is_in_bounds


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

    @property
    def row_count(self) -> int:
        return self.row_end - self.row_start

    @property
    def column_count(self) -> int:
        return self.column_end - self.column_start


def build_array_cells(parameters: ArrayLayerParameters) -> list[ArrayCell]:
    cells: list[ArrayCell] = []

    for row in range(parameters.rows):
        center_y = (row - (parameters.rows - 1) / 2) * parameters.pitch_y
        for column in range(parameters.columns):
            center_x = (column - (parameters.columns - 1) / 2) * parameters.pitch_x
            present, group = _cell_state(parameters, row, column)
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
        -parameters.columns * parameters.pitch_x / 2 + region.column_start * parameters.pitch_x
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
) -> tuple[bool, str]:
    if not isinstance(parameters, SolderBallParameters):
        return (True, "array")

    omitted = {(cell.row, cell.column) for cell in parameters.omitted_cells}
    if (row, column) in omitted:
        return (False, "void")
    center = center_bounds(
        parameters.rows,
        parameters.columns,
        parameters.center_solder_rows,
        parameters.center_solder_columns,
    )
    if parameters.center_solder_enabled and is_in_bounds(row, column, center):
        return (True, "center")
    removal = center_bounds(
        parameters.rows,
        parameters.columns,
        parameters.removal_rows,
        parameters.removal_columns,
    )
    if parameters.solder_removal_enabled and is_in_bounds(row, column, removal):
        return (False, "void")
    if parameters.center_solder_enabled or parameters.solder_removal_enabled:
        return (True, "perimeter")
    return (True, "array")


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
