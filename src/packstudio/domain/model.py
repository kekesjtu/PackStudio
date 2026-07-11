from collections.abc import Sequence
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from packstudio.domain.geometry import AxisAlignedBlock, MetadataValue, find_overlapping_pairs
from packstudio.domain.materials import Material
from packstudio.domain.thermal import BoundaryCondition, HeatSource


class CoordinateSystem(BaseModel):
    model_config = ConfigDict(frozen=True)

    origin: str = "substrate bottom-face center"
    x_axis: str = "package length"
    y_axis: str = "package width"
    z_axis: str = "upward through package thickness"


class ModelGroup(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    name: str = Field(min_length=1, max_length=120)
    parent_id: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9._-]*$")
    block_ids: list[str] = Field(default_factory=list)


class PackageModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: Literal["packstudio.model/v1"] = "packstudio.model/v1"
    template_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    name: str = Field(min_length=1, max_length=160)
    length_unit: Literal["mm"] = "mm"
    coordinate_system: CoordinateSystem = Field(default_factory=CoordinateSystem)
    materials: list[Material]
    blocks: list[AxisAlignedBlock]
    groups: list[ModelGroup]
    heat_sources: list[HeatSource] = Field(default_factory=list)
    boundaries: list[BoundaryCondition] = Field(default_factory=list)
    metadata: dict[str, MetadataValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_references_and_geometry(self) -> "PackageModel":
        material_ids = _unique_ids(self.materials, "material")
        block_ids = _unique_ids(self.blocks, "block")
        group_ids = _unique_ids(self.groups, "group")
        _unique_ids(self.heat_sources, "heat source")
        _unique_ids(self.boundaries, "boundary")

        for block in self.blocks:
            if block.material_id not in material_ids:
                raise ValueError(
                    f"block {block.id} references unknown material {block.material_id}"
                )
            if block.parent_group_id not in group_ids:
                raise ValueError(
                    f"block {block.id} references unknown group {block.parent_group_id}"
                )

        for group in self.groups:
            if group.parent_id is not None and group.parent_id not in group_ids:
                raise ValueError(f"group {group.id} references unknown parent {group.parent_id}")
            unknown_blocks = set(group.block_ids) - block_ids
            if unknown_blocks:
                raise ValueError(
                    f"group {group.id} references unknown blocks {sorted(unknown_blocks)}"
                )
            _validate_group_ancestry(group, {item.id: item for item in self.groups})

        for source in self.heat_sources:
            if source.block_id not in block_ids:
                raise ValueError(
                    f"heat source {source.id} references unknown block {source.block_id}"
                )
        for boundary in self.boundaries:
            unknown_targets = {target.block_id for target in boundary.targets} - block_ids
            if unknown_targets:
                raise ValueError(
                    f"boundary {boundary.id} references unknown blocks {sorted(unknown_targets)}"
                )

        overlaps = find_overlapping_pairs(self.blocks)
        if overlaps:
            preview = ", ".join(f"{left}/{right}" for left, right in overlaps[:5])
            raise ValueError(f"model contains overlapping blocks: {preview}")
        return self


class _Identified(Protocol):
    id: str


def _unique_ids(items: Sequence[_Identified], label: str) -> set[str]:
    identifiers = [item.id for item in items]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"duplicate {label} id")
    return set(identifiers)


def _validate_group_ancestry(group: ModelGroup, groups: dict[str, ModelGroup]) -> None:
    seen = {group.id}
    parent_id = group.parent_id
    while parent_id is not None:
        if parent_id in seen:
            raise ValueError(f"group cycle includes {group.id}")
        seen.add(parent_id)
        parent_id = groups[parent_id].parent_id
