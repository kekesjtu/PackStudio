from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.core.baseline_materials import materials_for
from packstudio.templates.package_library.core.definitions import (
    TemplateDefinition,
    TemplateValues,
)
from packstudio.templates.package_library.core.generator import BuiltTemplate
from packstudio.templates.package_library.core.geometry import centered_draft
from packstudio.templates.package_library.core.material_options import (
    BOND_WIRES,
    DIE,
    selection,
)
from packstudio.templates.package_library.core.parameters import TemplateRequest
from packstudio.templates.package_library.core.primitives import four_direction_wire_drafts
from packstudio.templates.package_library.leadframe.fields import soic_fields
from packstudio.templates.package_library.leadframe.soic_primitives import (
    soic_leadframe_drafts,
    soic_tie_bar_drafts,
)


def definition() -> TemplateDefinition:
    return TemplateDefinition(
        id="soic_family",
        display_name="SOIC family",
        category="Lead-frame packages",
        fields=soic_fields(),
        builder=_build,
        material_selections=(
            selection(
                "group-encapsulant",
                "encapsulant",
                "塑封材料",
                "epoxy-mold",
                ("epoxy-mold", "eme-7730lf"),
            ),
            DIE,
            selection(
                "group-die-attach",
                "die",
                "芯片粘接材料",
                "dieattach-84-1lmis",
                ("dieattach-84-1lmis", "dieattach-2600bt"),
            ),
            selection(
                "group-die-flag",
                "leadframe",
                "芯片承载台材料",
                "leadframe-c194",
                ("leadframe-c194", "copper"),
            ),
            selection(
                "group-tie-bars",
                "leadframe",
                "Tie bar 材料",
                "leadframe-c194",
                ("leadframe-c194", "copper"),
            ),
            selection(
                "group-lead-frame",
                "leadframe",
                "引线框材料",
                "leadframe-c194",
                ("leadframe-c194", "copper"),
            ),
            BOND_WIRES,
            selection(
                "group-exposed-pad",
                "options",
                "暴露焊盘材料",
                "leadframe-c194",
                ("leadframe-c194", "copper"),
                visible_when={"exposed_pad.enabled": True},
            ),
        ),
    )


def _build(values: TemplateValues, _request: TemplateRequest) -> BuiltTemplate:
    overall_width = values.number("package.width")
    body_length = values.number("body.length")
    body_width = values.number("body.width")
    standoff = values.number("package.standoff")
    flag_length = values.number("flag.length")
    flag_width = values.number("flag.width")
    flag_thickness = values.number("flag.thickness")
    die_length = values.number("die.length")
    die_width = values.number("die.width")
    die_thickness = values.number("die.thickness")
    lead_thickness = values.number("leads.thickness")
    lead_z = standoff + values.number("leads.height")
    lead_top = lead_z + lead_thickness
    flag_z = lead_z - values.number("flag.downset")
    die_z = flag_z + lead_thickness
    die_top = die_z + die_thickness
    diameter = values.number("bond_wire.diameter")
    lead_count = values.integer("leads.total")
    wire_x_end = flag_length / 2 + values.number("leads.gap")
    wire_y_end = flag_width / 2 + values.number("leads.gap")
    die_above_leads = die_top > lead_top
    wire_x_vertical = wire_x_end if die_above_leads else die_length / 2 - diameter
    wire_y_vertical = wire_y_end if die_above_leads else die_width / 2 - diameter
    _validate(values)

    drafts = [
        centered_draft(
            "encapsulant",
            "SOIC encapsulant",
            StructureType.ENCAPSULANT,
            (body_length, body_width, values.number("body.thickness")),
            standoff,
            "epoxy-mold",
            "group-encapsulant",
            "Encapsulant",
            priority=100,
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
        centered_draft(
            "die-flag",
            "Die flag",
            StructureType.LEAD_FRAME,
            (flag_length, flag_width, flag_thickness),
            flag_z,
            "soic-die-flag",
            "group-die-flag",
            "Die flag",
        ),
        *soic_tie_bar_drafts(
            body_length,
            flag_length,
            values.number("tie_bar.width"),
            flag_z,
            flag_thickness,
        ),
        *four_direction_wire_drafts(
            "bond-wire",
            die_length,
            die_width,
            wire_x_end,
            wire_y_end,
            wire_x_vertical,
            wire_y_vertical,
            die_width,
            die_length,
            max(die_top, lead_top) - diameter,
            min(die_top, lead_top),
            abs(lead_top - die_top),
            diameter,
            "soic-bondwire-x",
            "soic-bondwire-y",
        ),
        *soic_leadframe_drafts(
            overall_width,
            body_width,
            flag_length,
            flag_width,
            values.number("leads.gap"),
            lead_count // 2,
            values.number("leads.pitch"),
            values.number("leads.width"),
            lead_thickness,
            lead_z,
            values.number("leads.foot_length"),
        ),
        centered_draft(
            "die-attach",
            "Die attach",
            StructureType.DIE_ATTACH,
            (die_length, die_width, values.number("die.attach")),
            die_z,
            "dieattach-84-1lmis",
            "group-die-attach",
            "Die attach",
        ),
    ]
    if values.boolean("exposed_pad.enabled"):
        thickness = values.number("exposed_pad.thickness")
        drafts.append(
            centered_draft(
                "exposed-pad",
                "Exposed thermal pad",
                StructureType.EXPOSED_PAD,
                (flag_length, flag_width, thickness),
                -thickness,
                "leadframe-c194",
                "group-exposed-pad",
                "Exposed pad",
            )
        )
    return BuiltTemplate(
        drafts=drafts,
        materials=materials_for("soic_family"),
        power_w=values.number("die.power"),
        metadata={
            "lead_count": lead_count,
            "reference_baseline": "FloTHERM PACK 2504 SOP_8_3_81x4_93",
            "exposed_pad_enabled": values.boolean("exposed_pad.enabled"),
        },
    )


def _validate(values: TemplateValues) -> None:
    if values.integer("leads.total") % 2:
        raise ValueError("SOIC total lead count must be even")
    if values.number("body.width") > values.number("package.width"):
        raise ValueError("SOIC body must fit inside the lead envelope")
    if max(values.number("flag.length"), values.number("die.length")) > values.number(
        "body.length"
    ):
        raise ValueError("die and flag must fit inside the SOIC body")
    if max(values.number("flag.width"), values.number("die.width")) > values.number("body.width"):
        raise ValueError("die and flag must fit inside the SOIC body")
