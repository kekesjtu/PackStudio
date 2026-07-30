from dataclasses import dataclass

from packstudio.domain.geometry import AxisAlignedBlock
from packstudio.domain.materials import Material


@dataclass(frozen=True)
class LayerBuild:
    blocks: list[AxisAlignedBlock]
    materials: list[Material]
    group_names: dict[str, str]
    metadata: dict[str, str | int | float | bool]
