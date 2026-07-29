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
        id="qfn",
        display_name="QFN",
        category="Lead-frame packages",
        fields=(
            number("package.length", "package", "封装长度", 12, 2, 30),
            number("package.width", "package", "封装宽度", 12, 2, 30),
            number("package.standoff", "package", "底部焊料厚度", 0.05, 0.01, 0.3),
            number("encapsulant.thickness", "encapsulant", "塑封厚度", 0.85, 0.2, 5),
            number("die.length", "die", "芯片长度", 5.4, 0.2, 25),
            number("die.width", "die", "芯片宽度", 5.4, 0.2, 25),
            number("die.thickness", "die", "芯片厚度", 0.25, 0.03, 1.5),
            number("die.attach", "die", "粘接层厚度", 0.025, 0.005, 0.3),
            number("die.power", "die", "芯片功率", 0, 0, 1000, "W"),
            number("pad.length", "leadframe", "DAP 长度", 10.8, 0.5, 28),
            number("pad.width", "leadframe", "DAP 宽度", 10.8, 0.5, 28),
            number("pad.thickness", "leadframe", "DAP 厚度", 0.2, 0.03, 1),
            integer("leads.count_x", "leadframe", "上下侧引脚数", 25, 1, 100),
            integer("leads.count_y", "leadframe", "左右侧引脚数", 25, 1, 100),
            number("leads.pitch", "leadframe", "引脚间距", 0.4, 0.1, 2),
            number("leads.width", "leadframe", "引脚宽度", 0.2, 0.03, 1),
            number("leads.length", "leadframe", "暴露引脚长度", 0.5, 0.05, 3),
            number("bond_wire.diameter", "bond_wires", "键合线等效宽度", 0.03, 0.01, 0.2),
            toggle("thermal_land.enabled", "options", "包含底部散热焊盘"),
            number(
                "thermal_land.thickness",
                "options",
                "散热焊盘厚度",
                0.1,
                0.01,
                1,
                visible_when={"thermal_land.enabled": True},
            ),
        ),
        builder=_build,
    )


def _build(values: TemplateValues, _request: TemplateRequest) -> BuiltTemplate:
    length = values.number("package.length")
    width = values.number("package.width")
    standoff = values.number("package.standoff")
    die_length = values.number("die.length")
    die_width = values.number("die.width")
    die_thickness = values.number("die.thickness")
    attach = values.number("die.attach")
    pad_length = values.number("pad.length")
    pad_width = values.number("pad.width")
    pad_thickness = values.number("pad.thickness")
    lead_width = values.number("leads.width")
    lead_length = values.number("leads.length")
    pitch = values.number("leads.pitch")
    count_x = values.integer("leads.count_x")
    count_y = values.integer("leads.count_y")
    if max(die_length, pad_length) > length or max(die_width, pad_width) > width:
        raise ValueError("die and DAP must fit inside the QFN body")
    if (count_x - 1) * pitch + lead_width > length:
        raise ValueError("top/bottom QFN leads do not fit the package length")
    if (count_y - 1) * pitch + lead_width > width:
        raise ValueError("left/right QFN leads do not fit the package width")

    die_z = pad_thickness + attach
    drafts = [
        centered_draft(
            "encapsulant",
            "QFN encapsulant",
            StructureType.ENCAPSULANT,
            (length, width, values.number("encapsulant.thickness")),
            0,
            "eme-7730lf",
            "group-encapsulant",
            "Encapsulant",
            priority=100,
        ),
        centered_draft(
            "dap",
            "Die attach pad",
            StructureType.EXPOSED_PAD,
            (pad_length, pad_width, pad_thickness),
            0,
            "leadframe-c194",
            "group-exposed-pad",
            "Exposed pad",
        ),
        centered_draft(
            "dap-solder",
            "Exposed pad solder",
            StructureType.SOLDER,
            (pad_length, pad_width, standoff),
            -standoff,
            "solder-sn63",
            "group-solder",
            "Solder",
        ),
        centered_draft(
            "die-attach",
            "Die attach",
            StructureType.DIE_ATTACH,
            (die_length, die_width, attach),
            pad_thickness,
            "high-k-die-attach",
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
            min(length - 2 * lead_length, die_length + 5.5),
            min(width - 2 * lead_length, die_width + 5.5),
            die_z + die_thickness,
            values.number("bond_wire.diameter"),
        ),
    ]
    drafts.extend(
        _qfn_leads(
            length,
            width,
            count_x,
            count_y,
            pitch,
            lead_width,
            lead_length,
            pad_thickness,
            standoff,
        )
    )
    if values.boolean("thermal_land.enabled"):
        land = values.number("thermal_land.thickness")
        drafts.append(
            centered_draft(
                "thermal-land",
                "Thermal land",
                StructureType.EXPOSED_PAD,
                (pad_length, pad_width, land),
                -standoff - land,
                "copper",
                "group-exposed-pad",
                "Exposed pad",
            )
        )
    return BuiltTemplate(
        drafts=drafts,
        power_w=values.number("die.power"),
        metadata={
            "lead_count": 2 * count_x + 2 * count_y,
            "thermal_land_enabled": values.boolean("thermal_land.enabled"),
        },
    )


def _qfn_leads(
    length: float,
    width: float,
    count_x: int,
    count_y: int,
    pitch: float,
    lead_width: float,
    lead_length: float,
    lead_thickness: float,
    solder_thickness: float,
) -> list:
    drafts = []
    for column in range(count_x):
        x = (column - (count_x - 1) / 2) * pitch
        for side, direction in (("bottom", -1), ("top", 1)):
            y = direction * (width / 2 - lead_length / 2)
            drafts.extend(
                _lead_pair(
                    f"qfn-{side}-{column + 1}",
                    x,
                    y,
                    (lead_width, lead_length),
                    lead_thickness,
                    solder_thickness,
                )
            )
    for row in range(count_y):
        y = (row - (count_y - 1) / 2) * pitch
        for side, direction in (("left", -1), ("right", 1)):
            x = direction * (length / 2 - lead_length / 2)
            drafts.extend(
                _lead_pair(
                    f"qfn-{side}-{row + 1}",
                    x,
                    y,
                    (lead_length, lead_width),
                    lead_thickness,
                    solder_thickness,
                )
            )
    return drafts


def _lead_pair(
    identifier: str,
    center_x: float,
    center_y: float,
    footprint: tuple[float, float],
    lead_thickness: float,
    solder_thickness: float,
) -> list:
    return [
        centered_draft(
            f"{identifier}-lead",
            "QFN lead",
            StructureType.LEAD_FRAME,
            (*footprint, lead_thickness),
            0,
            "leadframe-c194",
            "group-lead-frame",
            "Lead frame",
            center_x=center_x,
            center_y=center_y,
        ),
        centered_draft(
            f"{identifier}-solder",
            "QFN lead solder",
            StructureType.SOLDER,
            (*footprint, solder_thickness),
            -solder_thickness,
            "solder-sn63",
            "group-solder",
            "Solder",
            center_x=center_x,
            center_y=center_y,
        ),
    ]
