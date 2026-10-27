from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ConductivityTensor(BaseModel):
    model_config = ConfigDict(frozen=True)

    x: float = Field(ge=0)
    y: float = Field(ge=0)
    z: float = Field(ge=0)

    @classmethod
    def isotropic(cls, conductivity: float) -> "ConductivityTensor":
        return cls(x=conductivity, y=conductivity, z=conductivity)


class Material(BaseModel):
    model_config = ConfigDict(frozen=True, allow_inf_nan=False)

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    name: str = Field(min_length=1, max_length=120)
    conductivity: ConductivityTensor
    density: float = Field(gt=0, description="kg/m^3")
    specific_heat: float = Field(gt=0, description="J/(kg*K)")
    color: str = Field(default="#8A94A6", pattern=r"^#[0-9A-Fa-f]{6}$")
    source: str | None = Field(default=None, max_length=300)
    conductivity_coefficient: float | None = None
    conductivity_reference_temperature_c: float | None = None

    @model_validator(mode="after")
    def validate_temperature_law(self):
        if (self.conductivity_coefficient is None) != (
            self.conductivity_reference_temperature_c is None
        ):
            raise ValueError("温度相关导热率需要系数和参考温度")
        return self

    @field_validator("conductivity", mode="before")
    @classmethod
    def expand_isotropic_conductivity(cls, value: Any) -> Any:
        if isinstance(value, int | float):
            return ConductivityTensor.isotropic(float(value))
        return value
