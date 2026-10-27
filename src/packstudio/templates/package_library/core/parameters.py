from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from packstudio.domain.materials import Material
from packstudio.templates.package_library.core.array_parameters import (
    ArrayRepresentation,
    CellIndex,
)
from packstudio.templates.package_library.core.via_configuration import ViaConfiguration

type TemplateValue = str | int | float | bool | None


class BallMapPoint(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)
    id: str = Field(min_length=1, max_length=120)
    x: float
    y: float


class PackageSummary(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)
    part_number: str = ""
    vendor: str = ""
    max_power_w: float | None = Field(default=None, ge=0)
    max_junction_temperature_c: float | None = None
    max_case_temperature_c: float | None = None
    notes: str = ""


class BgaConfiguration(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    representation: ArrayRepresentation | Literal["isotropic"] | None = None
    center_solder_enabled: bool = False
    center_solder_rows: int | None = Field(default=None, ge=1)
    center_solder_columns: int | None = Field(default=None, ge=1)
    solder_removal_enabled: bool = False
    depopulated_center: bool | None = None
    removal_rows: int | None = Field(default=None, ge=0)
    removal_columns: int | None = Field(default=None, ge=0)
    omitted_cells: list[CellIndex] = Field(default_factory=list)
    allow_asymmetric_regions: bool = False
    staggered: bool = False
    center_staggered: bool = False
    populated_rows: int | None = Field(default=None, ge=0)
    populated_columns: int | None = Field(default=None, ge=0)
    ball_map_enabled: bool = False
    ball_map: list[BallMapPoint] = Field(default_factory=list)


class TemplateRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    template_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    design_name: str | None = Field(default=None, max_length=160)
    summary: PackageSummary = Field(default_factory=PackageSummary)
    overrides: dict[str, TemplateValue] = Field(default_factory=dict)
    bga: BgaConfiguration | None = None
    vias: ViaConfiguration | None = None
    material_assignments: dict[str, str] = Field(default_factory=dict)
    custom_materials: list[Material] = Field(default_factory=list)
    die_power_w: float | None = Field(default=None, ge=0)
