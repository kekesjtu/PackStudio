from dataclasses import dataclass, field

from packstudio.domain.enums import StructureType
from packstudio.domain.geometry import (
    BOOLEAN_SOURCE_ID_KEY,
    BOOLEAN_SOURCE_NAME_KEY,
    AxisAlignedBlock,
    Point3D,
    Size3D,
)


@dataclass(frozen=True)
class DraftBlock:
    id: str
    name: str
    structure_type: StructureType
    origin: tuple[float, float, float]
    size: tuple[float, float, float]
    material_id: str | None
    group_id: str
    group_name: str
    priority: int = 20
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)

    @property
    def maximum(self) -> tuple[float, float, float]:
        return tuple(a + b for a, b in zip(self.origin, self.size, strict=True))

    @property
    def volume(self) -> float:
        return self.size[0] * self.size[1] * self.size[2]


@dataclass(frozen=True)
class NormalizedDrafts:
    blocks: list[AxisAlignedBlock]
    group_names: dict[str, str]


def centered_draft(
    identifier: str,
    name: str,
    structure_type: StructureType,
    size: tuple[float, float, float],
    z: float,
    material_id: str,
    group_id: str,
    group_name: str,
    *,
    priority: int = 20,
    center_x: float = 0,
    center_y: float = 0,
    metadata: dict[str, str | int | float | bool] | None = None,
) -> DraftBlock:
    return DraftBlock(
        id=identifier,
        name=name,
        structure_type=structure_type,
        origin=(center_x - size[0] / 2, center_y - size[1] / 2, z),
        size=size,
        material_id=material_id,
        group_id=group_id,
        group_name=group_name,
        priority=priority,
        metadata=metadata or {},
    )


def corner_draft(
    identifier: str,
    name: str,
    structure_type: StructureType,
    origin: tuple[float, float, float],
    size: tuple[float, float, float],
    material_id: str,
    group_id: str,
    group_name: str,
    *,
    priority: int = 20,
    metadata: dict[str, str | int | float | bool] | None = None,
) -> DraftBlock:
    return DraftBlock(
        id=identifier,
        name=name,
        structure_type=structure_type,
        origin=origin,
        size=size,
        material_id=material_id,
        group_id=group_id,
        group_name=group_name,
        priority=priority,
        metadata=metadata or {},
    )


def preserve_drafts(drafts: list[DraftBlock]) -> NormalizedDrafts:
    """Keep PACK cuboids, including intentional overlaps, in source order."""
    return NormalizedDrafts(
        blocks=[
            AxisAlignedBlock(
                id=f"{draft.id}-part-1",
                name=draft.name,
                structure_type=draft.structure_type,
                origin=Point3D(**dict(zip("xyz", draft.origin, strict=True))),
                size=Size3D(**dict(zip("xyz", draft.size, strict=True))),
                material_id=draft.material_id,
                parent_group_id=draft.group_id,
                metadata={
                    **draft.metadata,
                    BOOLEAN_SOURCE_ID_KEY: draft.id,
                    BOOLEAN_SOURCE_NAME_KEY: draft.name,
                },
            )
            for draft in drafts
        ],
        group_names={draft.group_id: draft.group_name for draft in drafts},
    )
