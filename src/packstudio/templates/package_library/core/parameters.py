from pydantic import BaseModel, ConfigDict, Field

from packstudio.default_parameters import request_default
from packstudio.domain.materials import Material
from packstudio.templates.flip_chip_cbga.parameters import (
    ArrayRepresentation,
    CellIndex,
    MeshParameters,
)

type TemplateValue = str | int | float | bool | None


class BgaConfiguration(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    representation: ArrayRepresentation = Field(
        default_factory=lambda: request_default("bga", "representation"), validate_default=True
    )
    center_solder_enabled: bool = Field(
        default_factory=lambda: request_default("bga", "center_solder_enabled")
    )
    center_solder_rows: int = Field(
        default_factory=lambda: request_default("bga", "center_solder_rows"), ge=1
    )
    center_solder_columns: int = Field(
        default_factory=lambda: request_default("bga", "center_solder_columns"), ge=1
    )
    solder_removal_enabled: bool = Field(
        default_factory=lambda: request_default("bga", "solder_removal_enabled")
    )
    removal_rows: int = Field(default_factory=lambda: request_default("bga", "removal_rows"), ge=0)
    removal_columns: int = Field(
        default_factory=lambda: request_default("bga", "removal_columns"), ge=0
    )
    omitted_cells: list[CellIndex] = Field(default_factory=list)
    allow_asymmetric_regions: bool = Field(
        default_factory=lambda: request_default("bga", "allow_asymmetric_regions")
    )


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
