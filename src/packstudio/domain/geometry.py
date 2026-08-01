from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

from packstudio.domain.enums import StructureType

MetadataValue = str | int | float | bool
BOOLEAN_SOURCE_ID_KEY = "boolean_source_id"
BOOLEAN_SOURCE_NAME_KEY = "boolean_source_name"


class Point3D(BaseModel):
    model_config = ConfigDict(frozen=True)

    x: float
    y: float
    z: float


class Size3D(BaseModel):
    model_config = ConfigDict(frozen=True)

    x: float = Field(gt=0)
    y: float = Field(gt=0)
    z: float = Field(gt=0)


class AxisAlignedBlock(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    name: str = Field(min_length=1, max_length=160)
    structure_type: StructureType
    origin: Point3D
    size: Size3D
    material_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    parent_group_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    metadata: dict[str, MetadataValue] = Field(default_factory=dict)

    @property
    def max_x(self) -> float:
        return self.origin.x + self.size.x

    @property
    def max_y(self) -> float:
        return self.origin.y + self.size.y

    @property
    def max_z(self) -> float:
        return self.origin.z + self.size.z


class RectangleOperation(BaseModel):
    """One additive or subtractive XY rectangle in an extruded solid."""

    model_config = ConfigDict(frozen=True)

    add: bool
    x: float
    y: float
    width: float = Field(gt=0)
    height: float = Field(gt=0)


class RectangularBooleanBlock(BaseModel):
    """An extruded XY boolean profile used inside a PTA geometric layer."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    name: str = Field(min_length=1, max_length=160)
    structure_type: StructureType
    z: float
    thickness: float = Field(gt=0)
    material_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    parent_group_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    operations: list[RectangleOperation] = Field(min_length=1)
    source_block_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_operation_order(self) -> "RectangularBooleanBlock":
        if not self.operations[0].add:
            raise ValueError("boolean block must start with an additive rectangle")
        subtraction_started = False
        for operation in self.operations:
            if not operation.add:
                subtraction_started = True
            elif subtraction_started:
                raise ValueError("additive rectangles must precede subtractive rectangles")
        return self


def find_overlapping_pairs(
    blocks: Sequence[AxisAlignedBlock], tolerance: float = 1e-9
) -> list[tuple[str, str]]:
    """Find positive-volume intersections; touching faces are valid."""
    active: list[AxisAlignedBlock] = []
    overlaps: list[tuple[str, str]] = []

    for current in sorted(blocks, key=lambda block: block.origin.x):
        active = [
            candidate for candidate in active if candidate.max_x > current.origin.x + tolerance
        ]
        for candidate in active:
            if _intervals_overlap(
                candidate.origin.y, candidate.max_y, current.origin.y, current.max_y, tolerance
            ) and _intervals_overlap(
                candidate.origin.z, candidate.max_z, current.origin.z, current.max_z, tolerance
            ):
                overlaps.append((candidate.id, current.id))
        active.append(current)

    return overlaps


def _intervals_overlap(
    first_min: float,
    first_max: float,
    second_min: float,
    second_max: float,
    tolerance: float,
) -> bool:
    return min(first_max, second_max) > max(first_min, second_min) + tolerance
