from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.definitions import (
    TemplateDefinition,
    TemplateValues,
)
from packstudio.templates.package_library.fields import integer, number, toggle
from packstudio.templates.package_library.generator import BuiltTemplate
from packstudio.templates.package_library.geometry import centered_draft
from packstudio.templates.package_library.parameters import TemplateRequest
from packstudio.templates.package_library.primitives import bond_wire_drafts


def definition() -> TemplateDefinition:
    return TemplateDefinition(
        id="soic_family",
        display_name="SOIC family",
        category="Lead-frame packages",
        fields=(
            number("package.length", "package", "封装长度", 4.93, 2, 30),
            number("package.width", "package", "引脚外包络宽度", 6, 2, 30),
            number("package.standoff", "package", "离板高度", 0.15, 0, 1),
            number("body.width", "encapsulant", "塑封宽度", 3.81, 1, 25),
            number("body.thickness", "encapsulant", "塑封厚度", 1.47, 0.3, 6),
            number("die.length", "die", "芯片长度", 1.479, 0.2, 20),
            number("die.width", "die", "芯片宽度", 1.143, 0.2, 20),
            number("die.thickness", "die", "芯片厚度", 0.38, 0.03, 2),
            number("die.attach", "die", "粘接层厚度", 0.038, 0.005, 0.3),
            number("die.power", "die", "芯片功率", 0, 0, 1000, "W"),
            number("flag.length", "leadframe", "芯片承载台长度", 1.7748, 0.3, 25),
            number("flag.width", "leadframe", "芯片承载台宽度", 1.3716, 0.3, 20),
            integer("leads.total", "leadframe", "引脚总数", 8, 2, 100),
            number("leads.pitch", "leadframe", "引脚间距", 1.27, 0.1, 3),
            number("leads.width", "leadframe", "引脚宽度", 0.4, 0.03, 1.5),
            number("leads.thickness", "leadframe", "引脚厚度", 0.2, 0.03, 1),
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
    length = values.number("package.length")
    overall_width = values.number("package.width")
    body_width = values.number("body.width")
    standoff = values.number("package.standoff")
    flag_length = values.number("flag.length")
    flag_width = values.number("flag.width")
    die_length = values.number("die.length")
    die_width = values.number("die.width")
    die_thickness = values.number("die.thickness")
    attach = values.number("die.attach")
    lead_count = values.integer("leads.total")
    if lead_count % 2:
        raise ValueError("SOIC total lead count must be even")
    if body_width > overall_width:
        raise ValueError("SOIC body must fit inside the lead envelope")
    if max(flag_length, die_length) > length or max(flag_width, die_width) > body_width:
        raise ValueError("die and flag must fit inside the SOIC body")
    per_side = lead_count // 2
    pitch = values.number("leads.pitch")
    lead_width = values.number("leads.width")
    if (per_side - 1) * pitch + lead_width > length:
        raise ValueError("SOIC leads do not fit the package length")
    lead_thickness = values.number("leads.thickness")
    flag_z = standoff + 0.235
    die_z = flag_z + lead_thickness + attach
    drafts = [
        centered_draft(
            "encapsulant",
            "SOIC encapsulant",
            StructureType.ENCAPSULANT,
            (length, body_width, values.number("body.thickness")),
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
        *bond_wire_drafts(
            "bond-wire",
            die_length,
            die_width,
            min(length, die_length + 0.6),
            min(body_width, die_width + 0.6),
            die_z + die_thickness,
            values.number("bond_wire.diameter"),
        ),
        *_two_side_leads(
            per_side,
            pitch,
            lead_width,
            length,
            body_width,
            overall_width,
            standoff,
            lead_thickness,
        ),
    ]
    drafts.extend(_tie_bars(flag_length, flag_width, length, flag_z, lead_thickness))
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
            "lead_count": lead_count,
            "exposed_pad_enabled": values.boolean("exposed_pad.enabled"),
        },
    )


def _two_side_leads(
    per_side: int,
    pitch: float,
    width: float,
    length: float,
    body_width: float,
    overall_width: float,
    z: float,
    thickness: float,
) -> list:
    lead_length = (overall_width - body_width) / 2 + width
    drafts = []
    for index in range(per_side):
        x = (index - (per_side - 1) / 2) * pitch
        for side, direction in (("bottom", -1), ("top", 1)):
            y = direction * (body_width / 2 + lead_length / 2 - width / 2)
            drafts.append(
                centered_draft(
                    f"soic-lead-{side}-{index + 1}",
                    f"{side.title()} lead {index + 1}",
                    StructureType.LEAD_FRAME,
                    (width, lead_length, thickness),
                    z,
                    "leadframe-c194",
                    "group-lead-frame",
                    "Lead frame",
                    center_x=x,
                    center_y=y,
                )
            )
    return drafts


def _tie_bars(
    flag_length: float,
    flag_width: float,
    body_length: float,
    z: float,
    thickness: float,
) -> list:
    span = max((body_length - flag_length) / 2, 0.2)
    return [
        centered_draft(
            f"tie-{side}",
            f"{side.title()} tie bar",
            StructureType.LEAD_FRAME,
            (span, min(0.4, flag_width), thickness),
            z,
            "leadframe-c194",
            "group-lead-frame",
            "Lead frame",
            center_x=direction * (flag_length / 2 + span / 2),
        )
        for side, direction in (("left", -1), ("right", 1))
    ]
