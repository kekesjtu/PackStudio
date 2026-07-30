from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.core.geometry import DraftBlock, corner_draft


def qfn_interconnect_drafts(
    package_length: float,
    package_width: float,
    count_x: int,
    count_y: int,
    pitch_x: float,
    pitch_y: float,
    lead_width: float,
    exposed_length: float,
    exposed_thickness: float,
    lead_thickness: float,
    etch: float,
    standoff: float,
) -> list[DraftBlock]:
    drafts: list[DraftBlock] = []
    upper_thickness = lead_thickness - exposed_thickness
    if upper_thickness <= 0:
        raise ValueError("QFN lead thickness must exceed exposed lead thickness")
    for index in range(count_x):
        x = (index - (count_x - 1) / 2) * pitch_x - lead_width / 2
        for side, y, upper_y in (
            ("lower", -package_width / 2, -package_width / 2),
            (
                "upper",
                package_width / 2 - exposed_length,
                package_width / 2 - exposed_length - etch,
            ),
        ):
            drafts.extend(
                _lead_stack(
                    f"{side}-{index + 1}",
                    (x, y),
                    (x, upper_y),
                    (lead_width, exposed_length),
                    (lead_width, exposed_length + etch),
                    standoff,
                    exposed_thickness,
                    upper_thickness,
                )
            )
    for index in range(count_y):
        y = (index - (count_y - 1) / 2) * pitch_y - lead_width / 2
        for side, x, upper_x in (
            ("left", -package_length / 2, -package_length / 2),
            (
                "right",
                package_length / 2 - exposed_length,
                package_length / 2 - exposed_length - etch,
            ),
        ):
            drafts.extend(
                _lead_stack(
                    f"{side}-{index + 1}",
                    (x, y),
                    (upper_x, y),
                    (exposed_length, lead_width),
                    (exposed_length + etch, lead_width),
                    standoff,
                    exposed_thickness,
                    upper_thickness,
                )
            )
    return drafts


def _lead_stack(
    suffix: str,
    lower_xy: tuple[float, float],
    upper_xy: tuple[float, float],
    lower_size: tuple[float, float],
    upper_size: tuple[float, float],
    standoff: float,
    exposed_thickness: float,
    upper_thickness: float,
) -> list[DraftBlock]:
    records = (
        (
            f"solder-{suffix}",
            f"Solder {suffix}",
            StructureType.SOLDER,
            (*lower_xy, 0),
            (*lower_size, standoff),
            "solder-sn63",
            "group-solder",
            "Solder",
        ),
        (
            f"lead-lower-{suffix}",
            f"Lead lower {suffix}",
            StructureType.LEAD_FRAME,
            (*lower_xy, standoff),
            (*lower_size, exposed_thickness),
            "leadframe-c194",
            "group-lead-frame",
            "Lead frame",
        ),
        (
            f"lead-upper-{suffix}",
            f"Lead upper {suffix}",
            StructureType.LEAD_FRAME,
            (*upper_xy, standoff + exposed_thickness),
            (*upper_size, upper_thickness),
            "leadframe-c194",
            "group-lead-frame",
            "Lead frame",
        ),
    )
    return [corner_draft(*record) for record in records]
