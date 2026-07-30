from dataclasses import dataclass, field, replace

from packstudio.domain.enums import StructureType
from packstudio.domain.geometry import AxisAlignedBlock, Point3D, Size3D

_TOLERANCE = 1e-9


@dataclass(frozen=True)
class DraftBlock:
    id: str
    name: str
    structure_type: StructureType
    origin: tuple[float, float, float]
    size: tuple[float, float, float]
    material_id: str
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


def normalize_drafts(drafts: list[DraftBlock]) -> NormalizedDrafts:
    accepted: list[DraftBlock] = []
    for source in sorted(drafts, key=lambda item: (item.priority, item.volume, item.id)):
        remaining = [source]
        for blocker in accepted:
            remaining = [
                piece for candidate in remaining for piece in _subtract(candidate, blocker)
            ]
            if not remaining:
                break
        accepted.extend(remaining)

    counters: dict[str, int] = {}
    blocks: list[AxisAlignedBlock] = []
    for piece in accepted:
        counters[piece.id] = counters.get(piece.id, 0) + 1
        part = counters[piece.id]
        blocks.append(
            AxisAlignedBlock(
                id=f"{piece.id}-part-{part}",
                name=piece.name if part == 1 else f"{piece.name} part {part}",
                structure_type=piece.structure_type,
                origin=Point3D(
                    x=piece.origin[0],
                    y=piece.origin[1],
                    z=piece.origin[2],
                ),
                size=Size3D(x=piece.size[0], y=piece.size[1], z=piece.size[2]),
                material_id=piece.material_id,
                parent_group_id=piece.group_id,
                metadata=piece.metadata,
            )
        )
    return NormalizedDrafts(
        blocks=blocks,
        group_names={piece.group_id: piece.group_name for piece in accepted},
    )


def _subtract(candidate: DraftBlock, blocker: DraftBlock) -> list[DraftBlock]:
    candidate_max = candidate.maximum
    blocker_max = blocker.maximum
    low = tuple(max(candidate.origin[index], blocker.origin[index]) for index in range(3))
    high = tuple(min(candidate_max[index], blocker_max[index]) for index in range(3))
    if any(high[index] <= low[index] + _TOLERANCE for index in range(3)):
        return [candidate]

    x0, y0, z0 = candidate.origin
    x1, y1, z1 = candidate_max
    ix0, iy0, iz0 = low
    ix1, iy1, iz1 = high
    boxes = [
        ((x0, y0, z0), (ix0 - x0, y1 - y0, z1 - z0)),
        ((ix1, y0, z0), (x1 - ix1, y1 - y0, z1 - z0)),
        ((ix0, y0, z0), (ix1 - ix0, iy0 - y0, z1 - z0)),
        ((ix0, iy1, z0), (ix1 - ix0, y1 - iy1, z1 - z0)),
        ((ix0, iy0, z0), (ix1 - ix0, iy1 - iy0, iz0 - z0)),
        ((ix0, iy0, iz1), (ix1 - ix0, iy1 - iy0, z1 - iz1)),
    ]
    return [
        replace(candidate, origin=origin, size=size)
        for origin, size in boxes
        if min(size) > _TOLERANCE
    ]
