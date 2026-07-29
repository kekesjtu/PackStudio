from pydantic import BaseModel, ConfigDict, Field

from packstudio.domain.materials import Material
from packstudio.templates.flip_chip_cbga.parameters import (
    ArrayRepresentation,
    CellIndex,
    EnvironmentParameters,
    MeshParameters,
)

type TemplateValue = str | int | float | bool | None


class BgaConfiguration(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    representation: ArrayRepresentation = ArrayRepresentation.EQUIVALENT
    center_solder_enabled: bool = False
    center_solder_rows: int = Field(default=1, ge=1)
    center_solder_columns: int = Field(default=1, ge=1)
    solder_removal_enabled: bool = False
    removal_rows: int = Field(default=3, ge=1)
    removal_columns: int = Field(default=3, ge=1)
    omitted_cells: list[CellIndex] = Field(default_factory=list)


class TemplateRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    template_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    design_name: str | None = Field(default=None, max_length=160)
    overrides: dict[str, TemplateValue] = Field(default_factory=dict)
    bga: BgaConfiguration | None = None
    material_assignments: dict[str, str] = Field(default_factory=dict)
    custom_materials: list[Material] = Field(default_factory=list)
    die_power_w: float | None = Field(default=None, ge=0)
    mesh: MeshParameters = Field(default_factory=MeshParameters)
    environment: EnvironmentParameters = Field(default_factory=EnvironmentParameters)
