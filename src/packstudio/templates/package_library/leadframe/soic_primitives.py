from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.core.geometry import DraftBlock, corner_draft


def soic_leadframe_drafts(
    overall_width: float,
    body_width: float,
    flag_length: float,
    flag_width: float,
    gap: float,
    per_side: int,
    pitch: float,
    lead_width: float,
    lead_thickness: float,
    lead_z: float,
    foot_length: float,
) -> list[DraftBlock]:
    span_x = (per_side - 1) * pitch + lead_width
    outer_x = span_x / 2
    inner_x = flag_length / 2 + gap
    inner_y = flag_width / 2 + gap
    body_y = body_width / 2
    outer_y = overall_width / 2 - foot_length + lead_thickness
    bend_y = overall_width / 2 - foot_length
    if min(outer_x - inner_x, body_y - inner_y, outer_y - body_y) <= 0:
        raise ValueError("SOIC lead-frame dimensions are inconsistent")
    common = (StructureType.LEAD_FRAME, "group-lead-frame", "Lead frame")
    records = (
        (
            "inner-right",
            (inner_x, -inner_y, lead_z),
            (outer_x - inner_x, 2 * inner_y, lead_thickness),
            "soic-leadframe-inner",
        ),
        (
            "inner-left",
            (-outer_x, -inner_y, lead_z),
            (outer_x - inner_x, 2 * inner_y, lead_thickness),
            "soic-leadframe-inner",
        ),
        (
            "inner-upper",
            (-outer_x, inner_y, lead_z),
            (span_x, body_y - inner_y, lead_thickness),
            "soic-leadframe-inner",
        ),
        (
            "inner-lower",
            (-outer_x, -body_y, lead_z),
            (span_x, body_y - inner_y, lead_thickness),
            "soic-leadframe-inner",
        ),
        (
            "outer-upper",
            (-outer_x, body_y, lead_z),
            (span_x, outer_y - body_y, lead_thickness),
            "soic-leadframe-outer",
        ),
        (
            "outer-lower",
            (-outer_x, -outer_y, lead_z),
            (span_x, outer_y - body_y, lead_thickness),
            "soic-leadframe-outer",
        ),
        (
            "bend-upper",
            (-outer_x, bend_y, lead_thickness),
            (span_x, lead_thickness, lead_z - lead_thickness),
            "soic-leadframe-outer",
        ),
        (
            "bend-lower",
            (-outer_x, -bend_y - lead_thickness, lead_thickness),
            (span_x, lead_thickness, lead_z - lead_thickness),
            "soic-leadframe-outer",
        ),
        (
            "foot-upper",
            (-outer_x, bend_y, 0),
            (span_x, foot_length, lead_thickness),
            "soic-leadframe-outer",
        ),
        (
            "foot-lower",
            (-outer_x, -overall_width / 2, 0),
            (span_x, foot_length, lead_thickness),
            "soic-leadframe-outer",
        ),
    )
    return [
        corner_draft(
            f"soic-{name}",
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


def soic_tie_bar_drafts(
    body_length: float,
    flag_length: float,
    bar_width: float,
    z: float,
    thickness: float,
) -> list[DraftBlock]:
    span = body_length / 2 - flag_length / 2
    if span <= 0:
        raise ValueError("SOIC tie bars must fit inside the body")
    return [
        corner_draft(
            f"tie-bar-{side}",
            f"Tie bar {side}",
            StructureType.LEAD_FRAME,
            (x, -bar_width / 2, z),
            (span, bar_width, thickness),
            "soic-die-flag",
            "group-tie-bars",
            "Tie bars",
        )
        for side, x in (
            ("right", flag_length / 2),
            ("left", -body_length / 2),
        )
    ]
