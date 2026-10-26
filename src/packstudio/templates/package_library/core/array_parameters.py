from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from packstudio.domain.materials import Material
from packstudio.templates.package_library.core.array_solder_style import validate_solder_style


class ArrayRepresentation(StrEnum):
    DISCRETE = "discrete"
    EQUIVALENT = "equivalent"


class CellIndex(BaseModel):
    model_config = ConfigDict(frozen=True)

    row: int = Field(ge=0)
    column: int = Field(ge=0)


class ArrayLayerParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rows: int = Field(ge=1, le=50)
    columns: int = Field(ge=1, le=50)
    pitch_x: float = Field(gt=0)
    pitch_y: float = Field(gt=0)
    diameter: float = Field(gt=0)
    height: float = Field(gt=0)
    footprint_x_override: float | None = Field(default=None, gt=0)
    footprint_y_override: float | None = Field(default=None, gt=0)
    representation: ArrayRepresentation = ArrayRepresentation.EQUIVALENT
    element_material: Material
    matrix_material: Material

    @property
    def footprint_x(self) -> float:
        return self.footprint_x_override or ((self.columns - 1) * self.pitch_x + self.diameter)

    @property
    def footprint_y(self) -> float:
        return self.footprint_y_override or ((self.rows - 1) * self.pitch_y + self.diameter)

    @model_validator(mode="after")
    def validate_layout(self) -> "ArrayLayerParameters":
        if self.diameter > min(self.pitch_x, self.pitch_y):
            raise ValueError("element diameter must not exceed either array pitch")
        return self


class SolderBallParameters(ArrayLayerParameters):
    center_solder_enabled: bool = False
    center_solder_rows: int | None = Field(default=None, ge=1)
    center_solder_columns: int | None = Field(default=None, ge=1)
    solder_removal_enabled: bool = False
    removal_rows: int | None = Field(default=None, ge=0)
    removal_columns: int | None = Field(default=None, ge=0)
    omitted_cells: list[CellIndex] = Field(default_factory=list)
    allow_asymmetric_regions: bool = False

    @model_validator(mode="after")
    def validate_solder_style(self) -> "SolderBallParameters":
        validate_solder_style(self)
        return self

