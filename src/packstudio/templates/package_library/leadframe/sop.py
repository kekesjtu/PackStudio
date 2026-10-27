from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.core.baseline_materials import materials_for
from packstudio.templates.package_library.core.default_library import (
    load_fields,
    load_material_selections,
)
from packstudio.templates.package_library.core.definitions import (
    TemplateDefinition,
    TemplateValues,
)
from packstudio.templates.package_library.core.generator import BuiltTemplate
from packstudio.templates.package_library.core.geometry import centered_draft
from packstudio.templates.package_library.core.parameters import TemplateRequest
from packstudio.templates.package_library.core.primitives import four_direction_wire_drafts
from packstudio.templates.package_library.leadframe.sop_primitives import (
    sop_leadframe_drafts,
    sop_tie_bar_drafts,
)


def definition() -> TemplateDefinition:
    fields = load_fields("sop")
    return TemplateDefinition(
        id="sop",
        display_name="SOP",
        category="Lead-frame packages",
        fields=fields,
        builder=_build,
        step_order=(
            "package_setup",
            "overall_package",
            "encapsulant",
            "die",
            "die_flag_tie_bars",
            "leadframe",
            "bond_wires",
            "thermal_land_solder",
        ),
        material_selections=load_material_selections("sop", fields),
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
    die_attach_z = flag_z + flag_thickness
    die_z = die_attach_z + values.number("die.attach")
    die_top = die_z + die_thickness
    diameter = values.number("bond_wire.diameter")
    lead_count = values.integer("leads.total")
    wire_x_end = flag_length / 2 + values.number("leads.gap")
    wire_y_end = flag_width / 2 + values.number("leads.gap")
    die_above_leads = die_top > lead_top
    wire_x_vertical = wire_x_end if die_above_leads else die_length / 2 - diameter
    wire_y_vertical = wire_y_end if die_above_leads else die_width / 2 - diameter
    _validate(values)
    if die_top > standoff + values.number("body.thickness"):
        raise ValueError("SOP die and attach must fit inside the encapsulant")

    drafts = [
        centered_draft(
            "encapsulant",
            "SOP encapsulant",
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
            "sop-die-flag",
            "group-die-flag",
            "Die flag",
        ),
        *sop_tie_bar_drafts(
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
            "sop-bondwire-x",
            "sop-bondwire-y",
            minimum_vertical_height=diameter / 4,
        ),
        *sop_leadframe_drafts(
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
            die_attach_z,
            "dieattach-84-1lmis",
            "group-die-attach",
            "Die attach",
        ),
    ]
    if values.boolean("thermal_land.enabled"):
        thickness = values.number("thermal_land.thickness")
        if standoff <= 0:
            raise ValueError("SOP thermal land solder requires a positive standoff")
        drafts.extend(
            [
                centered_draft(
                    "thermal-land",
                    "Thermal land",
                    StructureType.EXPOSED_PAD,
                    (flag_length, flag_width, thickness),
                    -thickness,
                    "leadframe-c194",
                    "group-thermal-land",
                    "Thermal land",
                ),
                centered_draft(
                    "thermal-solder",
                    "Thermal land solder",
                    StructureType.SOLDER,
                    (flag_length, flag_width, standoff),
                    0,
                    "solder-sn63",
                    "group-thermal-solder",
                    "Solder",
                ),
            ]
        )
    return BuiltTemplate(
        drafts=drafts,
        materials=materials_for("sop"),
        power_w=values.number("die.power"),
        metadata={
            "lead_count": lead_count,
            "reference_baseline": "FloTHERM PACK 2504 SOP_8_3_81x4_93",
            "thermal_land_and_solder_enabled": values.boolean("thermal_land.enabled"),
        },
    )


def _validate(values: TemplateValues) -> None:
    if values.integer("leads.total") % 2:
        raise ValueError("SOP total lead count must be even")
    if values.number("body.width") > values.number("package.width"):
        raise ValueError("SOP body must fit inside the lead envelope")
    if max(values.number("flag.length"), values.number("die.length")) > values.number(
        "body.length"
    ):
        raise ValueError("die and flag must fit inside the SOP body")
    if max(values.number("flag.width"), values.number("die.width")) > values.number("body.width"):
        raise ValueError("die and flag must fit inside the SOP body")
