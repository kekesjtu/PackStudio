from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.core.geometry import DraftBlock, centered_draft


def via_grid_drafts(
    prefix: str,
    rows: int,
    columns: int,
    pitch: float,
    diameter: float,
    z: float,
    height: float,
    *,
    center_x: float = 0,
    center_y: float = 0,
    material_id: str = "copper",
) -> list[DraftBlock]:
    drafts = []
    for row in range(rows):
        for column in range(columns):
            x = (column - (columns - 1) / 2) * pitch + center_x
            y = (row - (rows - 1) / 2) * pitch + center_y
            drafts.append(
                centered_draft(
                    f"{prefix}-r{row + 1}-c{column + 1}",
                    f"Thermal via {row + 1},{column + 1}",
                    StructureType.VIA,
                    (diameter, diameter, height),
                    z,
                    material_id,
                    "group-vias",
                    "Thermal vias",
                    center_x=x,
                    center_y=y,
                )
            )
    return drafts
