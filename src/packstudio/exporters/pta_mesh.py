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
    profile = str(model.metadata.get("mesh_resolution", "standard"))
    horizontal_divisions, vertical_divisions = _PROFILE_DIVISIONS.get(
        profile,
        _PROFILE_DIVISIONS["standard"],
    )
    extent_x = max(block.max_x for block in blocks) - min(block.origin.x for block in blocks)
    extent_y = max(block.max_y for block in blocks) - min(block.origin.y for block in blocks)
    return (
        extent_x / horizontal_divisions,
        extent_y / horizontal_divisions,
        thickness / vertical_divisions,
    )
