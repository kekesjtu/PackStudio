from typing import Protocol


class CellLocation(Protocol):
    row: int
    column: int


class SolderStyleValues(Protocol):
    rows: int
    columns: int
    center_solder_enabled: bool
    center_solder_rows: int
    center_solder_columns: int
    solder_removal_enabled: bool
    removal_rows: int
    removal_columns: int
    omitted_cells: list[CellLocation]


def validate_solder_style(parameters: SolderStyleValues) -> None:
    if parameters.center_solder_enabled:
        _validate_center_region(
            parameters,
            parameters.center_solder_rows,
            parameters.center_solder_columns,
            "center solder",
        )
    if parameters.solder_removal_enabled:
        _validate_center_region(
            parameters,
            parameters.removal_rows,
            parameters.removal_columns,
            "solder removal",
        )
    elif parameters.omitted_cells:
        raise ValueError("omitted_cells require solder removal to be enabled")
    if (
        parameters.center_solder_enabled
        and parameters.solder_removal_enabled
        and (
            parameters.center_solder_rows > parameters.removal_rows
            or parameters.center_solder_columns > parameters.removal_columns
        )
    ):
        raise ValueError("center solder region must fit inside the solder removal region")

    omitted = {(cell.row, cell.column) for cell in parameters.omitted_cells}
    if len(omitted) != len(parameters.omitted_cells):
        raise ValueError("omitted_cells must be unique")
    if any(row >= parameters.rows or column >= parameters.columns for row, column in omitted):
        raise ValueError("omitted cell lies outside the array")
    if not _has_present_solder(parameters, omitted):
        raise ValueError("solder style must retain at least one array element")


def center_bounds(
    rows: int,
    columns: int,
    region_rows: int,
    region_columns: int,
) -> tuple[int, int, int, int]:
    row_start = (rows - region_rows) // 2
    column_start = (columns - region_columns) // 2
    return (
        row_start,
        row_start + region_rows,
        column_start,
        column_start + region_columns,
    )


def is_in_bounds(row: int, column: int, bounds: tuple[int, int, int, int]) -> bool:
    row_start, row_end, column_start, column_end = bounds
    return row_start <= row < row_end and column_start <= column < column_end


def _validate_center_region(
    parameters: SolderStyleValues,
    region_rows: int,
    region_columns: int,
    label: str,
) -> None:
    if region_rows >= parameters.rows or region_columns >= parameters.columns:
        raise ValueError(f"{label} region must be smaller than the full array")
    if (parameters.rows - region_rows) % 2 or (parameters.columns - region_columns) % 2:
        raise ValueError(f"{label} region must be symmetric about the array center")


def _has_present_solder(
    parameters: SolderStyleValues,
    omitted: set[tuple[int, int]],
) -> bool:
    center = center_bounds(
        parameters.rows,
        parameters.columns,
        parameters.center_solder_rows,
        parameters.center_solder_columns,
    )
    removal = center_bounds(
        parameters.rows,
        parameters.columns,
        parameters.removal_rows,
        parameters.removal_columns,
    )
    for row in range(parameters.rows):
        for column in range(parameters.columns):
            if (row, column) in omitted:
                continue
            if parameters.center_solder_enabled and is_in_bounds(row, column, center):
                return True
            if not parameters.solder_removal_enabled or not is_in_bounds(row, column, removal):
                return True
    return False
