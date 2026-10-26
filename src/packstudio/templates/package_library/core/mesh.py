"""Shared mesh controls for all package templates."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from packstudio.runtime_data import request_default


class MeshResolution(StrEnum):
    COARSE = "coarse"
    STANDARD = "standard"
    FINE = "fine"


class MeshParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    resolution: MeshResolution = Field(
        default_factory=lambda: request_default("mesh", "resolution"), validate_default=True
    )
