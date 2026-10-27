"""PACK's drop-in slug: raised centre, horizontal ring, legs and feet."""

from math import pi, sqrt

from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.core.geometry import centered_draft
from packstudio.templates.package_library.core.primitives import rectangular_ring_drafts


def append_slug(drafts, values, substrate_top):
    if not values.matches({"cover.type": "encapsulant", "slug.enabled": True}):
        return
    length, width = values.number("slug.length"), values.number("slug.width")
    thickness = values.number("slug.thickness")
    side = sqrt(pi) * values.number("slug.diameter") / 2
    offset, clearance = values.number("slug.offset"), values.number("slug.clearance")
    encap_height = (
        values.number("bumps.height") + values.number("die.thickness")
        if values.boolean("cover.flush")
        else values.number("cover.thickness")
    )
    top = substrate_top + encap_height
    horizontal_z = top - thickness - offset
    foot_z = substrate_top + values.number("bumps.height") + clearance
    material_id, group, label = "aluminum", "group-slug", "Drop-in slug"
    drafts.append(
        centered_draft(
            "slug-top",
            "Slug top",
            StructureType.HEAT_SLUG,
            (side, side, thickness),
            top - thickness,
            material_id,
            group,
            label,
        )
    )
    drafts.extend(
        rectangular_ring_drafts(
            "slug-h",
            length,
            width,
            side,
            side,
            horizontal_z,
            thickness,
            StructureType.HEAT_SLUG,
            material_id,
            group,
            label,
        )
    )
    drafts.extend(
        rectangular_ring_drafts(
            "slug-v",
            length,
            width,
            length - 2 * thickness,
            width - 2 * thickness,
            foot_z,
            horizontal_z - foot_z,
            StructureType.HEAT_SLUG,
            material_id,
            group,
            label,
        )
    )
    tx = (values.number("slug.foot_length") - length) / 2
    ty = (values.number("slug.foot_width") - width) / 2
    for suffix, sx, sy, x, y in [
        ("right", tx, width, (length + tx) / 2, 0),
        ("left", tx, width, -(length + tx) / 2, 0),
        ("upper", length, ty, 0, (width + ty) / 2),
        ("lower", length, ty, 0, -(width + ty) / 2),
    ]:
        if min(sx, sy) <= 0:
            raise ValueError("散热块支脚外伸尺寸必须大于散热块外框")
        drafts.append(
            centered_draft(
                f"slug-foot-{suffix}",
                f"Slug foot {suffix}",
                StructureType.HEAT_SLUG,
                (sx, sy, thickness),
                foot_z,
                material_id,
                group,
                label,
                center_x=x,
                center_y=y,
            )
        )
        if values.boolean("slug.adhesive_enabled"):
            drafts.append(
                centered_draft(
                    f"slug-adhesive-{suffix}",
                    "Slug adhesive",
                    StructureType.DIE_ATTACH,
                    (
                        sx + thickness if suffix in {"left", "right"} else sx,
                        sy + thickness if suffix in {"upper", "lower"} else sy,
                        clearance,
                    ),
                    foot_z - clearance,
                    "stiffener-adhesive",
                    "group-slug-adhesive",
                    "Slug adhesive",
                    center_x=x
                    + (
                        thickness / 2
                        if suffix == "left"
                        else -thickness / 2
                        if suffix == "right"
                        else 0
                    ),
                    center_y=y
                    + (
                        thickness / 2
                        if suffix == "lower"
                        else -thickness / 2
                        if suffix == "upper"
                        else 0
                    ),
                )
            )
