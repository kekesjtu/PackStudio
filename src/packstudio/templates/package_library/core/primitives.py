from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.core.geometry import DraftBlock, corner_draft


def four_direction_wire_drafts(
    prefix: str,
    die_length: float,
    die_width: float,
    x_horizontal_end: float,
    y_horizontal_end: float,
    x_vertical_origin: float,
    y_vertical_origin: float,
    x_transverse_span: float,
    y_transverse_span: float,
    horizontal_z: float,
    vertical_z: float,
    vertical_height: float,
    diameter: float,
    material_x: str,
    material_y: str,
    *,
    x_enabled: bool = True,
    y_enabled: bool = True,
    minimum_vertical_height: float = 0,
) -> list[DraftBlock]:
    x_length = x_horizontal_end - die_length / 2
    y_length = y_horizontal_end - die_width / 2
    if (x_enabled and x_length <= 0) or (y_enabled and y_length <= 0) or vertical_height < 0:
        raise ValueError("FloXML bond-wire cuboids must have positive dimensions")
    common = {
        "structure_type": StructureType.BOND_WIRE,
        "group_id": "group-bond-wires",
        "group_name": "Bond wires",
    }
    drafts = [
        corner_draft(
            f"{prefix}-h-right",
            "Bond wires horizontal right",
            origin=(die_length / 2, -x_transverse_span / 2, horizontal_z),
            size=(x_length, x_transverse_span, diameter),
            material_id=material_x,
            **common,
        ),
        corner_draft(
            f"{prefix}-h-left",
            "Bond wires horizontal left",
            origin=(-x_horizontal_end, -x_transverse_span / 2, horizontal_z),
            size=(x_length, x_transverse_span, diameter),
            material_id=material_x,
            **common,
        ),
        corner_draft(
            f"{prefix}-h-upper",
            "Bond wires horizontal upper",
            origin=(-y_transverse_span / 2, die_width / 2, horizontal_z),
            size=(y_transverse_span, y_length, diameter),
            material_id=material_y,
            **common,
        ),
        corner_draft(
            f"{prefix}-h-lower",
            "Bond wires horizontal lower",
            origin=(-y_transverse_span / 2, -y_horizontal_end, horizontal_z),
            size=(y_transverse_span, y_length, diameter),
            material_id=material_y,
            **common,
        ),
        corner_draft(
            f"{prefix}-v-right",
            "Bond wires vertical right",
            origin=(x_vertical_origin, -x_transverse_span / 2, vertical_z),
            size=(diameter, x_transverse_span, vertical_height),
            material_id=material_x,
            **common,
        ),
        corner_draft(
            f"{prefix}-v-left",
            "Bond wires vertical left",
            origin=(-x_vertical_origin - diameter, -x_transverse_span / 2, vertical_z),
            size=(diameter, x_transverse_span, vertical_height),
            material_id=material_x,
            **common,
        ),
        corner_draft(
            f"{prefix}-v-upper",
            "Bond wires vertical upper",
            origin=(-y_transverse_span / 2, y_vertical_origin, vertical_z),
            size=(y_transverse_span, diameter, vertical_height),
            material_id=material_y,
            **common,
        ),
        corner_draft(
            f"{prefix}-v-lower",
            "Bond wires vertical lower",
            origin=(-y_transverse_span / 2, -y_vertical_origin - diameter, vertical_z),
            size=(y_transverse_span, diameter, vertical_height),
            material_id=material_y,
            **common,
        ),
    ]
    # Two-sided packages have no wires on the absent sides. Coplanar terminals
    # need horizontal wires only, rather than zero-height vertical cuboids.
    return [
        draft
        for draft in drafts
        if (x_enabled or draft.id.endswith(("upper", "lower")))
        and (y_enabled or draft.id.endswith(("left", "right")))
        and (vertical_height > minimum_vertical_height or not draft.id.startswith(f"{prefix}-v-"))
    ]


def rectangular_ring_drafts(
    prefix: str,
    outer_length: float,
    outer_width: float,
    inner_length: float,
    inner_width: float,
    z: float,
    thickness: float,
    structure_type: StructureType,
    material_id: str,
    group_id: str,
    group_name: str,
) -> list[DraftBlock]:
    if inner_length >= outer_length or inner_width >= outer_width:
        raise ValueError("ring opening must fit inside its outer rectangle")
    side = (outer_length - inner_length) / 2
    end = (outer_width - inner_width) / 2
    return [
        corner_draft(
            f"{prefix}-left",
            f"{group_name} left",
            structure_type,
            (-outer_length / 2, -outer_width / 2, z),
            (side, outer_width, thickness),
            material_id,
            group_id,
            group_name,
        ),
        corner_draft(
            f"{prefix}-right",
            f"{group_name} right",
            structure_type,
            (inner_length / 2, -outer_width / 2, z),
            (side, outer_width, thickness),
            material_id,
            group_id,
            group_name,
        ),
        corner_draft(
            f"{prefix}-lower",
            f"{group_name} lower",
            structure_type,
            (-inner_length / 2, -outer_width / 2, z),
            (inner_length, end, thickness),
            material_id,
            group_id,
            group_name,
        ),
        corner_draft(
            f"{prefix}-upper",
            f"{group_name} upper",
            structure_type,
            (-inner_length / 2, inner_width / 2, z),
            (inner_length, end, thickness),
            material_id,
            group_id,
            group_name,
        ),
    ]
