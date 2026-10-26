"""Shared centered-region and explicit-cell depopulation for thermal vias."""

from pydantic import BaseModel, ConfigDict, Field

from packstudio.templates.package_library.core.array_parameters import CellIndex


class ViaConfiguration(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    removal_enabled: bool = False
    removal_rows: int | None = Field(default=None, ge=0)
    removal_columns: int | None = Field(default=None, ge=0)
    omitted_cells: list[CellIndex] = Field(default_factory=list)

    def omissions(self, rows: int, columns: int) -> set[tuple[int, int]]:
        if not self.removal_enabled:
            return set()
        if self.removal_rows is None or self.removal_columns is None:
            raise ValueError("via removal requires both row and column counts")
        if self.removal_rows > rows or self.removal_columns > columns:
            raise ValueError("via removal region must fit inside the array")
        if (self.removal_rows == 0) != (self.removal_columns == 0):
            raise ValueError("via removal region dimensions must both be zero or positive")
        cells = {(cell.row, cell.column) for cell in self.omitted_cells}
        if any(row >= rows or column >= columns for row, column in cells):
            raise ValueError("omitted via cell is outside the array")
        row_start = (rows - self.removal_rows) // 2
        column_start = (columns - self.removal_columns) // 2
        cells.update(
            (row, column)
            for row in range(row_start, row_start + self.removal_rows)
            for column in range(column_start, column_start + self.removal_columns)
        )
        return cells
