from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

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
    material_id: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9._-]*$")
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
