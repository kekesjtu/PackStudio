from packstudio.domain.geometry import AxisAlignedBlock
from packstudio.domain.model import PackageModel

_PROFILE_DIVISIONS = {
    "coarse": (12, 1),
    "standard": (24, 2),
    "fine": (40, 4),
}


def layer_mesh_sizes(
    model: PackageModel,
    blocks: list[AxisAlignedBlock],
    thickness: float,
) -> tuple[float, float, float]:
    """Return non-zero PTA maximum mesh sizes for one geometric layer."""
    extent_x = max(block.max_x for block in blocks) - min(block.origin.x for block in blocks)
    extent_y = max(block.max_y for block in blocks) - min(block.origin.y for block in blocks)
    return geometry_mesh_sizes(model, extent_x, extent_y, thickness)


def geometry_mesh_sizes(
    model: PackageModel,
    extent_x: float,
    extent_y: float,
    extent_z: float,
) -> tuple[float, float, float]:
    profile = str(model.metadata.get("mesh_resolution", "standard"))
    horizontal_divisions, vertical_divisions = _PROFILE_DIVISIONS.get(
        profile,
        _PROFILE_DIVISIONS["standard"],
    )
    return (
        extent_x / horizontal_divisions,
        extent_y / horizontal_divisions,
        extent_z / vertical_divisions,
    )
