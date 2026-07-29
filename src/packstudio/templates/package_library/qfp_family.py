from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.definitions import (
    TemplateDefinition,
    TemplateValues,
)
from packstudio.templates.package_library.fields import integer, number, toggle
from packstudio.templates.package_library.generator import BuiltTemplate
from packstudio.templates.package_library.geometry import centered_draft
from packstudio.templates.package_library.parameters import TemplateRequest
from packstudio.templates.package_library.primitives import (
    bond_wire_drafts,
    four_side_lead_drafts,
)


def definition() -> TemplateDefinition:
    return TemplateDefinition(
        id="qfp_family",
        display_name="QFP family",
        category="Lead-frame packages",
        fields=(
            number("package.length", "package", "引脚外包络长度", 9, 3, 50),
            number("package.width", "package", "引脚外包络宽度", 9, 3, 50),
            number("package.standoff", "package", "离板高度", 0.1, 0, 1),
            number("body.length", "encapsulant", "塑封长度", 7, 2, 45),
            number("body.width", "encapsulant", "塑封宽度", 7, 2, 45),
            number("body.thickness", "encapsulant", "塑封厚度", 1.4, 0.3, 6),
            number("die.length", "die", "芯片长度", 2.1, 0.2, 30),
            number("die.width", "die", "芯片宽度", 2.1, 0.2, 30),
            number("die.thickness", "die", "芯片厚度", 0.35, 0.03, 2),
            number("die.attach", "die", "粘接层厚度", 0.038, 0.005, 0.3),
            number("die.power", "die", "芯片功率", 0, 0, 1000, "W"),
            number("flag.length", "leadframe", "芯片承载台长度", 2.94, 0.5, 35),
            number("flag.width", "leadframe", "芯片承载台宽度", 2.94, 0.5, 35),
            integer("leads.count_x", "leadframe", "上下侧引脚数", 8, 1, 100),
            integer("leads.count_y", "leadframe", "左右侧引脚数", 8, 1, 100),
            number("leads.pitch", "leadframe", "引脚间距", 0.8, 0.1, 3),
            number("leads.width", "leadframe", "引脚宽度", 0.4, 0.03, 1.5),
            number("leads.thickness", "leadframe", "引脚厚度", 0.15, 0.03, 1),
            number("bond_wire.diameter", "bond_wires", "键合线等效宽度", 0.03, 0.01, 0.2),
            toggle("exposed_pad.enabled", "options", "包含暴露焊盘"),
            number(
                "exposed_pad.thickness",
                "options",
                "暴露焊盘厚度",
                0.1,
                0.01,
                1,
                visible_when={"exposed_pad.enabled": True},
            ),
        ),
        builder=_build,
    )


def _build(values: TemplateValues, _request: TemplateRequest) -> BuiltTemplate:
    package_length = values.number("package.length")
    package_width = values.number("package.width")
    body_length = values.number("body.length")
    body_width = values.number("body.width")
    standoff = values.number("package.standoff")
    flag_length = values.number("flag.length")
    flag_width = values.number("flag.width")
    die_length = values.number("die.length")
    die_width = values.number("die.width")
    die_thickness = values.number("die.thickness")
    attach = values.number("die.attach")
    lead_thickness = values.number("leads.thickness")
    if body_length > package_length or body_width > package_width:
        raise ValueError("QFP body must fit inside the lead envelope")
    if max(flag_length, die_length) > body_length or max(flag_width, die_width) > body_width:
        raise ValueError("die and flag must fit inside the QFP body")
    flag_z = standoff + 0.375
    die_z = flag_z + lead_thickness + attach
    drafts = [
        centered_draft(
            "encapsulant",
            "QFP encapsulant",
            StructureType.ENCAPSULANT,
            (body_length, body_width, values.number("body.thickness")),
            standoff,
            "epoxy-mold",
            "group-encapsulant",
            "Encapsulant",
            priority=100,
        ),
        centered_draft(
            "die-flag",
            "Die flag",
            StructureType.LEAD_FRAME,
            (flag_length, flag_width, lead_thickness),
            flag_z,
            "leadframe-c194",
            "group-lead-frame",
            "Lead frame",
        ),
        centered_draft(
            "die-attach",
            "Die attach",
            StructureType.DIE_ATTACH,
            (die_length, die_width, attach),
            flag_z + lead_thickness,
            "die-attach",
            "group-die-attach",
            "Die attach",
        ),
        centered_draft(
            "die",
            "Silicon die",
            StructureType.DIE,
            (die_length, die_width, die_thickness),
            die_z,
            "silicon",
            "group-die",
            "Die",
        ),
        *four_side_lead_drafts(
            "qfp-lead",
            values.integer("leads.count_x"),
            values.integer("leads.count_y"),
            values.number("leads.pitch"),
            values.number("leads.width"),
            body_length,
            body_width,
            package_length,
            package_width,
            standoff,
            lead_thickness,
        ),
        *bond_wire_drafts(
            "bond-wire",
            die_length,
            die_width,
            min(body_length, die_length + 2),
            min(body_width, die_width + 2),
            die_z + die_thickness,
            values.number("bond_wire.diameter"),
        ),
    ]
    drafts.extend(
        _tie_bars(
            flag_length,
            flag_width,
            body_length,
            body_width,
            flag_z,
            lead_thickness,
        )
    )
    if values.boolean("exposed_pad.enabled"):
        thickness = values.number("exposed_pad.thickness")
        drafts.append(
            centered_draft(
                "exposed-pad",
                "Exposed thermal pad",
                StructureType.EXPOSED_PAD,
                (flag_length, flag_width, thickness),
                standoff - thickness,
                "copper",
                "group-exposed-pad",
                "Exposed pad",
            )
        )
    return BuiltTemplate(
        drafts=drafts,
        power_w=values.number("die.power"),
        metadata={
            "lead_count": 2 * values.integer("leads.count_x") + 2 * values.integer("leads.count_y"),
            "exposed_pad_enabled": values.boolean("exposed_pad.enabled"),
        },
    )


def _tie_bars(
    flag_length: float,
    flag_width: float,
    body_length: float,
    body_width: float,
    z: float,
    thickness: float,
) -> list:
    bar = min(0.5, flag_length / 4, flag_width / 4)
    x_span = max((body_length - flag_length) / 2, bar)
    y_span = max((body_width - flag_width) / 2, bar)
    return [
        centered_draft(
            "tie-left",
            "Left tie bar",
            StructureType.LEAD_FRAME,
            (x_span, bar, thickness),
            z,
            "leadframe-c194",
            "group-lead-frame",
            "Lead frame",
            center_x=-(flag_length / 2 + x_span / 2),
        ),
        centered_draft(
            "tie-right",
            "Right tie bar",
            StructureType.LEAD_FRAME,
            (x_span, bar, thickness),
            z,
            "leadframe-c194",
            "group-lead-frame",
            "Lead frame",
            center_x=flag_length / 2 + x_span / 2,
        ),
        centered_draft(
            "tie-bottom",
            "Bottom tie bar",
            StructureType.LEAD_FRAME,
            (bar, y_span, thickness),
            z,
            "leadframe-c194",
            "group-lead-frame",
            "Lead frame",
            center_y=-(flag_width / 2 + y_span / 2),
        ),
        centered_draft(
            "tie-top",
            "Top tie bar",
            StructureType.LEAD_FRAME,
            (bar, y_span, thickness),
            z,
            "leadframe-c194",
            "group-lead-frame",
            "Lead frame",
            center_y=flag_width / 2 + y_span / 2,
        ),
    ]
