from dataclasses import dataclass

from packstudio.domain.geometry import AxisAlignedBlock
from packstudio.domain.model import PackageModel
from packstudio.exporters.pta_boolean import (
    CompactedBooleanBlock,
    compact_boolean_blocks,
)

_TOLERANCE = 1e-9


@dataclass(frozen=True)
class PtaBooleanLayer:
    base_z: float
    thickness: float
    physical_blocks: list[AxisAlignedBlock]
    boolean_blocks: list[CompactedBooleanBlock]
    is_top: bool


def build_boolean_layers(
    model: PackageModel,
    source_density: dict[str, float],
) -> list[PtaBooleanLayer]:
    """Build bottom-to-top PTA layers while preserving PTA's top-layer Z rule.

    Only the top layer may contain blocks whose extrusion differs from the layer
    thickness.  Every lower layer therefore receives exact-height slices.  The top
    layer starts at the highest physical block origin; all geometry above that plane
    can share this layer while retaining its own extrusion height.
    """
    intervals = _occupied_intervals(model.blocks)
    top_base = max(block.origin.z for block in model.blocks)
    maximum_z = max(block.max_z for block in model.blocks)
    layers: list[PtaBooleanLayer] = []

    for base_z, interval_top, active_blocks in intervals:
        if base_z >= top_base - _TOLERANCE:
            continue
        if interval_top > top_base + _TOLERANCE:
            raise ValueError("PTA top layer base must coincide with a geometry boundary")
        slices = [_slice_block(block, base_z, interval_top) for block in active_blocks]
        layers.append(
            PtaBooleanLayer(
                base_z=base_z,
                thickness=interval_top - base_z,
                physical_blocks=slices,
                boolean_blocks=compact_boolean_blocks(slices, source_density),
                is_top=False,
            )
        )

    top_blocks = [
        _slice_block(block, top_base, block.max_z)
        for block in model.blocks
        if block.max_z > top_base + _TOLERANCE
    ]
    if not top_blocks:
        raise ValueError("PTA export requires at least one block in the top layer")
    layers.append(
        PtaBooleanLayer(
            base_z=top_base,
            thickness=maximum_z - top_base,
            physical_blocks=top_blocks,
            boolean_blocks=compact_boolean_blocks(top_blocks, source_density),
            is_top=True,
        )
    )
    _validate_layer_block_thicknesses(layers)
    return layers


def _occupied_intervals(
    blocks: list[AxisAlignedBlock],
) -> list[tuple[float, float, list[AxisAlignedBlock]]]:
    coordinates = sorted(
        {_snap(value) for block in blocks for value in (block.origin.z, block.max_z)}
    )
    intervals: list[tuple[float, float, list[AxisAlignedBlock]]] = []
    for base_z, interval_top in zip(coordinates, coordinates[1:], strict=False):
        if interval_top <= base_z + _TOLERANCE:
            continue
        active = [
            block
            for block in blocks
            if block.origin.z <= base_z + _TOLERANCE and block.max_z >= interval_top - _TOLERANCE
        ]
        if not active:
            raise ValueError("PTA export requires a contiguous stack without empty z intervals")
        intervals.append((base_z, interval_top, active))
    return intervals


def _slice_block(
    block: AxisAlignedBlock,
    base_z: float,
    maximum_z: float,
) -> AxisAlignedBlock:
    return block.model_copy(
        update={
            "origin": block.origin.model_copy(update={"z": base_z}),
            "size": block.size.model_copy(update={"z": maximum_z - base_z}),
        }
    )


def _validate_layer_block_thicknesses(layers: list[PtaBooleanLayer]) -> None:
    for layer in layers:
        for compacted in layer.boolean_blocks:
            block = compacted.geometry
            if abs(block.z - layer.base_z) > _TOLERANCE:
                raise ValueError("PTA layer block must start at its owning layer")
            if layer.is_top:
                if block.thickness > layer.thickness + _TOLERANCE:
                    raise ValueError("PTA top-layer block exceeds the top-layer envelope")
            elif abs(block.thickness - layer.thickness) > _TOLERANCE:
                raise ValueError("only PTA top-layer blocks may differ from layer thickness")


def _snap(value: float) -> float:
    return float(f"{value:.12g}")
