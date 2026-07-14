from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from packstudio.domain.materials import Material
from packstudio.templates.flip_chip_cbga.material_library import default_materials
from packstudio.templates.flip_chip_cbga.solder_style import validate_solder_style


class ArrayRepresentation(StrEnum):
    DISCRETE = "discrete"
    EQUIVALENT = "equivalent"


class MeshResolution(StrEnum):
    COARSE = "coarse"
    STANDARD = "standard"
    FINE = "fine"


class CellIndex(BaseModel):
    model_config = ConfigDict(frozen=True)

    row: int = Field(ge=0)
    column: int = Field(ge=0)


class RectangularPartParameters(BaseModel):
    model_config = ConfigDict(frozen=True)

    length: float = Field(gt=0, description="x size in mm")
    width: float = Field(gt=0, description="y size in mm")
    thickness: float = Field(gt=0, description="z size in mm")
    material: Material


class DieParameters(RectangularPartParameters):
    power_w: float = Field(default=1, ge=0)


class EncapsulantParameters(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = False
    length: float = Field(default=5, gt=0, description="x footprint in mm")
    width: float = Field(default=5, gt=0, description="y footprint in mm")
    cover_thickness: float = Field(default=0.3, gt=0, description="cover above die in mm")
    material: Material = Field(default_factory=lambda: default_materials()["encapsulant"])


class ArrayLayerParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rows: int = Field(ge=1, le=50)
    columns: int = Field(ge=1, le=50)
    pitch_x: float = Field(gt=0)
    pitch_y: float = Field(gt=0)
    diameter: float = Field(gt=0)
    height: float = Field(gt=0)
    representation: ArrayRepresentation = ArrayRepresentation.EQUIVALENT
    element_material: Material
    matrix_material: Material

    @property
    def footprint_x(self) -> float:
        return self.columns * self.pitch_x

    @property
    def footprint_y(self) -> float:
        return self.rows * self.pitch_y

    @model_validator(mode="after")
    def validate_layout(self) -> "ArrayLayerParameters":
        if self.diameter > min(self.pitch_x, self.pitch_y):
            raise ValueError("element diameter must not exceed either array pitch")
        return self


class SolderBallParameters(ArrayLayerParameters):
    center_solder_enabled: bool = False
    center_solder_rows: int = Field(default=3, ge=1)
    center_solder_columns: int = Field(default=3, ge=1)
    solder_removal_enabled: bool = False
    removal_rows: int = Field(default=5, ge=1)
    removal_columns: int = Field(default=5, ge=1)
    omitted_cells: list[CellIndex] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_solder_style(self) -> "SolderBallParameters":
        validate_solder_style(self)
        return self


class HeatSlugParameters(RectangularPartParameters):
    enabled: bool = False
    interface_thickness: float = Field(default=0.05, gt=0)
    interface_material: Material = Field(default_factory=lambda: default_materials()["tim"])


class LidParameters(RectangularPartParameters):
    enabled: bool = False
    interface_thickness: float = Field(default=0.05, gt=0)
    interface_material: Material = Field(default_factory=lambda: default_materials()["tim"])


class MeshParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    resolution: MeshResolution = MeshResolution.STANDARD


class EnvironmentParameters(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    ambient_temperature_k: float = Field(default=300, gt=0)
    default_convection_coefficient_w_m2k: float = Field(default=10, gt=0)
    pcb_convection_coefficient_w_m2k: float = Field(default=1600, gt=0)
    top_convection_coefficient_w_m2k: float = Field(default=10, gt=0)


class FlipChipCbgaParameters(BaseModel):
    model_config = ConfigDict(frozen=True)

    design_name: str = Field(default="Flip Chip CBGA", min_length=1, max_length=120)
    substrate: RectangularPartParameters = Field(default_factory=lambda: _default_substrate())
    die: DieParameters = Field(default_factory=lambda: _default_die())
    encapsulant: EncapsulantParameters = Field(default_factory=EncapsulantParameters)
    flip_chip_bumps: ArrayLayerParameters = Field(default_factory=lambda: _default_bumps())
    solder_balls: SolderBallParameters = Field(default_factory=lambda: _default_solder_balls())
    heat_slug: HeatSlugParameters = Field(default_factory=lambda: _default_heat_slug())
    lid: LidParameters = Field(default_factory=lambda: _default_lid())
    mesh: MeshParameters = Field(default_factory=MeshParameters)
    environment: EnvironmentParameters = Field(default_factory=EnvironmentParameters)

    @model_validator(mode="after")
    def validate_package_envelopes(self) -> "FlipChipCbgaParameters":
        tolerance = 1e-9
        if self.flip_chip_bumps.representation is not ArrayRepresentation.EQUIVALENT:
            raise ValueError("flip-chip bumps only support anisotropic equivalent representation")
        if self.solder_balls.matrix_material.id != "air":
            raise ValueError("BGA matrix material must be static air")
        if self.die.length > self.substrate.length + tolerance or self.die.width > (
            self.substrate.width + tolerance
        ):
            raise ValueError("die footprint must fit inside the substrate")
        if self.encapsulant.enabled:
            if (
                self.encapsulant.length <= self.die.length + tolerance
                or self.encapsulant.width <= self.die.width + tolerance
            ):
                raise ValueError("encapsulant footprint must extend beyond the die on every side")
            if (
                self.encapsulant.length > self.substrate.length + tolerance
                or self.encapsulant.width > self.substrate.width + tolerance
            ):
                raise ValueError("encapsulant footprint must fit inside the substrate")
        if self.flip_chip_bumps.footprint_x > self.die.length + tolerance or (
            self.flip_chip_bumps.footprint_y > self.die.width + tolerance
        ):
            raise ValueError("flip-chip bump array must fit inside the die footprint")
        if self.solder_balls.footprint_x > self.substrate.length + tolerance or (
            self.solder_balls.footprint_y > self.substrate.width + tolerance
        ):
            raise ValueError("solder-ball array must fit inside the substrate footprint")

        target_length, target_width = self.die.length, self.die.width
        if self.heat_slug.enabled:
            if self.heat_slug.length < target_length or self.heat_slug.width < target_width:
                raise ValueError("heat slug must cover the top-side target")
            if (
                self.heat_slug.length > self.substrate.length + tolerance
                or self.heat_slug.width > self.substrate.width + tolerance
            ):
                raise ValueError("heat slug must fit inside the substrate footprint")
            target_length, target_width = self.heat_slug.length, self.heat_slug.width
        if self.lid.enabled and (self.lid.length < target_length or self.lid.width < target_width):
            raise ValueError("lid must cover the top-side target")
        if self.lid.enabled and (
            self.lid.length > self.substrate.length + tolerance
            or self.lid.width > self.substrate.width + tolerance
        ):
            raise ValueError("lid must fit inside the substrate footprint")
        return self


def _default_substrate() -> RectangularPartParameters:
    return RectangularPartParameters(
        length=6,
        width=6,
        thickness=1.15,
        material=default_materials()["alumina"],
    )


def _default_die() -> DieParameters:
    return DieParameters(
        length=1.8,
        width=1.8,
        thickness=0.61,
        power_w=1,
        material=default_materials()["silicon"],
    )


def _default_bumps() -> ArrayLayerParameters:
    materials = default_materials()
    return ArrayLayerParameters(
        rows=7,
        columns=7,
        pitch_x=0.25,
        pitch_y=0.25,
        diameter=0.12,
        height=0.1,
        element_material=materials["solder"],
        matrix_material=materials["underfill"],
    )


def _default_solder_balls() -> SolderBallParameters:
    materials = default_materials()
    return SolderBallParameters(
        rows=7,
        columns=7,
        pitch_x=0.8,
        pitch_y=0.8,
        diameter=0.5,
        height=0.4,
        element_material=materials["solder"],
        matrix_material=materials["air"],
    )


def _default_heat_slug() -> HeatSlugParameters:
    return HeatSlugParameters(
        enabled=False,
        length=2.4,
        width=2.4,
        thickness=0.25,
        material=default_materials()["copper"],
    )


def _default_lid() -> LidParameters:
    return LidParameters(
        enabled=False,
        length=5.5,
        width=5.5,
        thickness=0.3,
        material=default_materials()["copper"],
    )
