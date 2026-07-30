from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.core.definitions import TemplateValues
from packstudio.templates.package_library.core.geometry import DraftBlock, centered_draft
from packstudio.templates.package_library.core.primitives import (
    rectangular_ring_drafts,
)


def append_top_structure(
    drafts: list[DraftBlock],
    values: TemplateValues,
    die_length: float,
    die_width: float,
    substrate_top: float,
    die_top: float,
) -> None:
    cover_type = values.text("cover.type")
    if cover_type == "encapsulant":
        drafts.append(
            centered_draft(
                "encapsulant",
                "Encapsulant",
                StructureType.ENCAPSULANT,
                (
                    values.number("cover.length"),
                    values.number("cover.width"),
                    values.number("cover.thickness"),
                ),
                substrate_top,
                "epoxy-mold",
                "group-encapsulant",
                "Encapsulant",
                priority=100,
            )
        )
    elif cover_type == "lid":
        _append_lid(drafts, values, die_length, die_width, substrate_top, die_top)
    elif cover_type == "plate":
        _append_plate(drafts, values, die_length, die_width, die_top)


def _append_lid(
    drafts: list[DraftBlock],
    values: TemplateValues,
    die_length: float,
    die_width: float,
    substrate_top: float,
    die_top: float,
) -> None:
    length = values.number("lid.length")
    width = values.number("lid.width")
    wall = values.number("lid.base_thickness")
    cavity_length = length - 2 * wall
    cavity_width = width - 2 * wall
    if min(cavity_length, cavity_width) <= 0:
        raise ValueError("lid side walls leave no central cavity")
    wall_height = die_top - substrate_top
    drafts.extend(
        (
            centered_draft(
                "lid",
                "Lid",
                StructureType.LID,
                (length, width, values.number("lid.thickness")),
                die_top,
                "aluminum",
                "group-lid",
                "Lid",
            ),
            *rectangular_ring_drafts(
                "lid-wall",
                length,
                width,
                cavity_length,
                cavity_width,
                substrate_top,
                wall_height,
                StructureType.LID,
                "aluminum",
                "group-lid",
                "Lid",
            ),
            *rectangular_ring_drafts(
                "lid-adhesive",
                length,
                width,
                cavity_length,
                cavity_width,
                substrate_top,
                values.number("lid.adhesive"),
                StructureType.DIE_ATTACH,
                "stiffener-adhesive",
                "group-lid-adhesive",
                "Lid adhesive",
            ),
            centered_draft(
                "lid-die-attach",
                "Lid die attach",
                StructureType.THERMAL_INTERFACE,
                (die_length, die_width, values.number("lid.die_attach")),
                die_top,
                "flip-cap-grease",
                "group-lid-die-attach",
                "Lid die attach",
            ),
        )
    )


def _append_plate(
    drafts: list[DraftBlock],
    values: TemplateValues,
    die_length: float,
    die_width: float,
    die_top: float,
) -> None:
    drafts.extend(
        (
            centered_draft(
                "thermal-plate",
                "Thermal plate",
                StructureType.HEAT_SLUG,
                (
                    values.number("plate.length"),
                    values.number("plate.width"),
                    values.number("plate.thickness"),
                ),
                die_top,
                "aluminum",
                "group-plate",
                "Thermal plate",
            ),
            centered_draft(
                "plate-die-attach",
                "Plate die attach",
                StructureType.THERMAL_INTERFACE,
                (die_length, die_width, values.number("plate.die_attach")),
                die_top,
                "flip-cap-grease",
                "group-plate-die-attach",
                "Plate die attach",
            ),
        )
    )
