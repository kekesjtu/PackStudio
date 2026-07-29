from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.geometry import DraftBlock, centered_draft


def bond_wire_drafts(
    prefix: str,
    die_length: float,
    die_width: float,
    extent_length: float,
    extent_width: float,
    z: float,
    diameter: float,
) -> list[DraftBlock]:
    drafts: list[DraftBlock] = []
    x_span = max((extent_length - die_length) / 2, diameter)
    y_span = max((extent_width - die_width) / 2, diameter)
    for side, direction in (("left", -1), ("right", 1)):
        center_x = direction * (die_length / 2 + x_span / 2)
        for index, center_y in enumerate((-die_width / 4, die_width / 4), start=1):
            drafts.append(
                centered_draft(
                    f"{prefix}-{side}-{index}",
                    f"Bond wire {side} {index}",
                    StructureType.BOND_WIRE,
                    (x_span, diameter, diameter),
                    z,
                    "gold",
                    "group-bond-wires",
                    "Bond wires",
                    center_x=center_x,
                    center_y=center_y,
                )
            )
    for side, direction in (("bottom", -1), ("top", 1)):
        center_y = direction * (die_width / 2 + y_span / 2)
        for index, center_x in enumerate((-die_length / 4, die_length / 4), start=1):
            drafts.append(
                centered_draft(
                    f"{prefix}-{side}-{index}",
                    f"Bond wire {side} {index}",
                    StructureType.BOND_WIRE,
                    (diameter, y_span, diameter),
                    z,
                    "gold",
                    "group-bond-wires",
                    "Bond wires",
                    center_x=center_x,
                    center_y=center_y,
                )
            )
    return drafts


def via_grid_drafts(
    prefix: str,
    rows: int,
    columns: int,
    pitch: float,
    diameter: float,
    z: float,
    height: float,
) -> list[DraftBlock]:
    drafts = []
    for row in range(rows):
        for column in range(columns):
            x = (column - (columns - 1) / 2) * pitch
            y = (row - (rows - 1) / 2) * pitch
            drafts.append(
                centered_draft(
                    f"{prefix}-r{row + 1}-c{column + 1}",
                    f"Thermal via {row + 1},{column + 1}",
                    StructureType.VIA,
                    (diameter, diameter, height),
                    z,
                    "copper",
                    "group-vias",
                    "Thermal vias",
                    center_x=x,
                    center_y=y,
                )
            )
    return drafts


def four_side_lead_drafts(
    prefix: str,
    count_x: int,
    count_y: int,
    pitch: float,
    width: float,
    body_length: float,
    body_width: float,
    overall_length: float,
    overall_width: float,
    z: float,
    thickness: float,
    material_id: str = "leadframe-c194",
) -> list[DraftBlock]:
    if overall_length < body_length or overall_width < body_width:
        raise ValueError("overall lead span must contain the package body")
    drafts: list[DraftBlock] = []
    lead_y = max((overall_width - body_width) / 2 + width, width)
    lead_x = max((overall_length - body_length) / 2 + width, width)
    for column in range(count_x):
        x = (column - (count_x - 1) / 2) * pitch
        for side, direction in (("bottom", -1), ("top", 1)):
            y = direction * (body_width / 2 + lead_y / 2 - width / 2)
            drafts.append(
                centered_draft(
                    f"{prefix}-{side}-{column + 1}",
                    f"{side.title()} lead {column + 1}",
                    StructureType.LEAD_FRAME,
                    (width, lead_y, thickness),
                    z,
                    material_id,
                    "group-lead-frame",
                    "Lead frame",
                    center_x=x,
                    center_y=y,
                )
            )
    for row in range(count_y):
        y = (row - (count_y - 1) / 2) * pitch
        for side, direction in (("left", -1), ("right", 1)):
            x = direction * (body_length / 2 + lead_x / 2 - width / 2)
            drafts.append(
                centered_draft(
                    f"{prefix}-{side}-{row + 1}",
                    f"{side.title()} lead {row + 1}",
                    StructureType.LEAD_FRAME,
                    (lead_x, width, thickness),
                    z,
                    material_id,
                    "group-lead-frame",
                    "Lead frame",
                    center_x=x,
                    center_y=y,
                )
            )
    return drafts
