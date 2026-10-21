"""Wirebond PBGA bottom trace opening and embedded backside spreader."""

from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.core.definitions import TemplateValues
from packstudio.templates.package_library.core.geometry import DraftBlock, centered_draft
from packstudio.templates.package_library.core.primitives import rectangular_ring_drafts


def bottom_layers(values: TemplateValues) -> list[DraftBlock]:
    length, width = values.number("package.length"), values.number("package.width")
    thickness = values.number("trace.bottom_thickness")
    z = values.number("bga.height")
    if not values.boolean("spreader.enabled"):
        return [
            centered_draft(
                "bottom-trace",
                "Bottom trace",
                StructureType.TRACE,
                (length, width, thickness),
                z,
                "wirebond-trace-bottom",
                "group-traces",
                "Bottom trace",
            )
        ]
    spreader_length = values.number("spreader.length")
    spreader_width = values.number("spreader.width")
    spreader_thickness = values.number("spreader.thickness")
    if spreader_length > length or spreader_width > width:
        raise ValueError("backside spreader must fit inside the substrate")
    if spreader_thickness > values.number("substrate.thickness"):
        raise ValueError("backside spreader must not extend above the substrate")
    return [
        *rectangular_ring_drafts(
            "bottom-trace",
            length,
            width,
            values.number("spreader.hole_length"),
            values.number("spreader.hole_width"),
            z,
            thickness,
            StructureType.TRACE,
            "wirebond-trace-bottom",
            "group-traces",
            "Bottom trace",
        ),
        centered_draft(
            "backside-spreader",
            "Backside spreader",
            StructureType.HEAT_SLUG,
            (spreader_length, spreader_width, spreader_thickness),
            z,
            "copper",
            "group-backside-spreader",
            "Backside spreader",
            priority=10,
        ),
    ]
