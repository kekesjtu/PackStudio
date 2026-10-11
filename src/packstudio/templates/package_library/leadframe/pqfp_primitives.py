from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.core.geometry import DraftBlock, corner_draft


def pqfp_leadframe_drafts(
    package_length: float,
    package_width: float,
    body_length: float,
    body_width: float,
    flag_length: float,
    flag_width: float,
    gap_x: float,
    gap_y: float,
    count_x: int,
    count_y: int,
    pitch: float,
    lead_width: float,
    lead_thickness: float,
    standoff: float,
    leadframe_height: float,
    foot_length: float,
) -> list[DraftBlock]:
    span_x = (count_x - 1) * pitch + lead_width
    span_y = (count_y - 1) * pitch + lead_width
    z = standoff + leadframe_height
    inner_x = flag_length / 2 + gap_x
    inner_y = flag_width / 2 + gap_y
    foot_width = foot_length - lead_thickness
    outer_x_end = package_length / 2 - foot_width
    outer_y_end = package_width / 2 - foot_width
    if min(foot_width, body_length / 2 - inner_x, body_width / 2 - inner_y) <= 0:
        raise ValueError("QFP lead-frame dimensions are inconsistent")
    return [
        *_four_sides(
            "pqfp-inner",
            inner_x,
            inner_y,
            body_length / 2,
            body_width / 2,
            span_x,
            span_y,
            z,
            lead_thickness,
            "pqfp-leadframe-inner-x",
            "pqfp-leadframe-inner-y",
        ),
        *_four_sides(
            "pqfp-outer",
            body_length / 2,
            body_width / 2,
            outer_x_end,
            outer_y_end,
            span_x,
            span_y,
            z,
            lead_thickness,
            "pqfp-leadframe-outer-x",
            "pqfp-leadframe-outer-y",
        ),
        *_pqfp_bends_and_feet(
            package_length,
            package_width,
            span_x,
            span_y,
            z,
            lead_thickness,
            foot_length,
            foot_width,
        ),
    ]


def _four_sides(
    prefix: str,
    inner_x: float,
    inner_y: float,
    outer_x: float,
    outer_y: float,
    span_x: float,
    span_y: float,
    z: float,
    thickness: float,
    material_x: str,
    material_y: str,
) -> list[DraftBlock]:
    common = (StructureType.LEAD_FRAME, "group-lead-frame", "Lead frame")
    return [
        corner_draft(
            f"{prefix}-right",
            "Lead frame right",
            common[0],
            (inner_x, -span_y / 2, z),
            (outer_x - inner_x, span_y, thickness),
            material_x,
            common[1],
            common[2],
        ),
        corner_draft(
            f"{prefix}-left",
            "Lead frame left",
            common[0],
            (-outer_x, -span_y / 2, z),
            (outer_x - inner_x, span_y, thickness),
            material_x,
            common[1],
            common[2],
        ),
        corner_draft(
            f"{prefix}-upper",
            "Lead frame upper",
            common[0],
            (-span_x / 2, inner_y, z),
            (span_x, outer_y - inner_y, thickness),
            material_y,
            common[1],
            common[2],
        ),
        corner_draft(
            f"{prefix}-lower",
            "Lead frame lower",
            common[0],
            (-span_x / 2, -outer_y, z),
            (span_x, outer_y - inner_y, thickness),
            material_y,
            common[1],
            common[2],
        ),
    ]


def _pqfp_bends_and_feet(
    package_length: float,
    package_width: float,
    span_x: float,
    span_y: float,
    z: float,
    thickness: float,
    foot_length: float,
    foot_width: float,
) -> list[DraftBlock]:
    x_bend = package_length / 2 - foot_length
    y_bend = package_width / 2 - foot_length
    common = (StructureType.LEAD_FRAME, "group-lead-frame", "Lead frame")
    records = [
        ("right", (x_bend, -span_y / 2, 0), (thickness, span_y, z), "pqfp-leadframe-outer-x"),
        (
            "left",
            (-x_bend - thickness, -span_y / 2, 0),
            (thickness, span_y, z),
            "pqfp-leadframe-outer-x",
        ),
        ("upper", (-span_x / 2, y_bend, 0), (span_x, thickness, z), "pqfp-leadframe-outer-y"),
        (
            "lower",
            (-span_x / 2, -y_bend - thickness, 0),
            (span_x, thickness, z),
            "pqfp-leadframe-outer-y",
        ),
        (
            "foot-right",
            (package_length / 2 - foot_width, -span_y / 2, 0),
            (foot_width, span_y, thickness),
            "pqfp-leadframe-outer-x",
        ),
        (
            "foot-left",
            (-package_length / 2, -span_y / 2, 0),
            (foot_width, span_y, thickness),
            "pqfp-leadframe-outer-x",
        ),
        (
            "foot-upper",
            (-span_x / 2, package_width / 2 - foot_width, 0),
            (span_x, foot_width, thickness),
            "pqfp-leadframe-outer-y",
        ),
        (
            "foot-lower",
            (-span_x / 2, -package_width / 2, 0),
            (span_x, foot_width, thickness),
            "pqfp-leadframe-outer-y",
        ),
    ]
    return [
        corner_draft(
            f"pqfp-{name}",
            f"Lead frame {name}",
            common[0],
            origin,
            size,
            material,
            common[1],
            common[2],
        )
        for name, origin, size, material in records
    ]


def pqfp_tie_bar_drafts(
    body_length: float,
    body_width: float,
    flag_length: float,
    flag_width: float,
    bar_width: float,
    z: float,
    thickness: float,
    plating_height: float,
) -> list[DraftBlock]:
    x_span = body_length / 2 - flag_length / 2
    y_span = body_width / 2 - flag_width / 2
    if min(x_span, y_span, plating_height) <= 0:
        raise ValueError("QFP tie-bar dimensions are inconsistent")
    x_records = (
        ("right-upper", flag_length / 2, flag_width / 2 - bar_width),
        ("left-upper", -body_length / 2, flag_width / 2 - bar_width),
        ("left-lower", -body_length / 2, -flag_width / 2),
        ("right-lower", flag_length / 2, -flag_width / 2),
    )
    y_records = (
        ("upper-right", flag_length / 2 - bar_width, flag_width / 2),
        ("upper-left", -flag_length / 2, flag_width / 2),
        ("lower-left", -flag_length / 2, -body_width / 2),
        ("lower-right", flag_length / 2 - bar_width, -body_width / 2),
    )
    footprints = [(name, (x, y), (x_span, bar_width)) for name, x, y in x_records] + [
        (name, (x, y), (bar_width, y_span)) for name, x, y in y_records
    ]
    drafts: list[DraftBlock] = []
    for name, origin, size in footprints:
        drafts.extend(
            (
                corner_draft(
                    f"tie-bar-{name}",
                    f"Tie bar {name}",
                    StructureType.LEAD_FRAME,
                    (*origin, z),
                    (*size, thickness),
                    "pqfp-tie-bar",
                    "group-tie-bars",
                    "Tie bars",
                ),
                corner_draft(
                    f"tie-bar-plate-{name}",
                    f"Tie-bar plate {name}",
                    StructureType.ENCAPSULANT,
                    (*origin, z + thickness),
                    (*size, plating_height),
                    "epoxy-mold",
                    "group-tie-bar-plates",
                    "Tie-bar plates",
                ),
            )
        )
    return drafts
