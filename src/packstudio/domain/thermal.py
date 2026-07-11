from pydantic import BaseModel, ConfigDict, Field, model_validator

from packstudio.domain.enums import BlockFace, BoundaryKind


class HeatSource(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    name: str = Field(min_length=1, max_length=120)
    block_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    power_w: float = Field(ge=0)


class SurfaceReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    block_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    face: BlockFace


class BoundaryCondition(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    name: str = Field(min_length=1, max_length=120)
    kind: BoundaryKind
    targets: list[SurfaceReference] = Field(min_length=1)
    temperature_k: float | None = Field(default=None, gt=0)
    heat_flux_w_m2: float | None = None
    convection_coefficient_w_m2k: float | None = Field(default=None, gt=0)
    ambient_temperature_k: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_kind_parameters(self) -> "BoundaryCondition":
        if self.kind is BoundaryKind.TEMPERATURE and self.temperature_k is None:
            raise ValueError("temperature boundary requires temperature_k")
        if self.kind is BoundaryKind.HEAT_FLUX and self.heat_flux_w_m2 is None:
            raise ValueError("heat-flux boundary requires heat_flux_w_m2")
        if self.kind is BoundaryKind.CONVECTION and (
            self.convection_coefficient_w_m2k is None or self.ambient_temperature_k is None
        ):
            raise ValueError("convection boundary requires coefficient and ambient temperature")
        return self
