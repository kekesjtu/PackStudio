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
from packstudio.templates.package_library.leadframe.pqfp_primitives import (
    pqfp_leadframe_drafts,
    pqfp_tie_bar_drafts,
)


def definition() -> TemplateDefinition:
    fields = load_fields("pqfp")
    return TemplateDefinition(
        id="pqfp",
        display_name="PQFP",
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
        material_selections=load_material_selections("pqfp", fields),
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
    lead_height = values.number("leads.height")
    lead_z = standoff + lead_height
    flag_z = lead_z - values.number("flag.downset")
    die_attach_z = flag_z + lead_thickness
    die_z = die_attach_z + attach
    die_top = die_z + die_thickness
    gap_x = values.number("leads.gap_x")
    gap_y = values.number("leads.gap_y")
    diameter = values.number("bond_wire.diameter")
    lead_top = lead_z + lead_thickness
    die_above_leads = die_top >= lead_top
    wire_height = abs(die_top - lead_top)
    if wire_height < 1e-12:
        wire_height = 0
    _validate(values)

    drafts = [
        centered_draft(
            "encapsulant",
            "PQFP encapsulant",
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
            (flag_length, flag_width, lead_thickness),
            flag_z,
            "pqfp-die-flag",
            "group-die-flag",
            "Die flag",
        ),
        *four_direction_wire_drafts(
            "bond-wire",
            die_length,
            die_width,
            flag_length / 2 + gap_x,
            flag_width / 2 + gap_y,
            flag_length / 2 + gap_x if die_above_leads else die_length / 2 - diameter,
            flag_width / 2 + gap_y if die_above_leads else die_width / 2 - diameter,
            die_width,
            die_length,
            max(die_top, lead_top) - diameter,
            min(die_top, lead_top),
            wire_height,
            diameter,
            "pqfp-bondwire-x",
            "pqfp-bondwire-y",
        ),
        *pqfp_leadframe_drafts(
            package_length,
            package_width,
            body_length,
            body_width,
            flag_length,
            flag_width,
            gap_x,
            gap_y,
            values.integer("leads.count_x"),
            values.integer("leads.count_y"),
            values.number("leads.pitch"),
            values.number("leads.width"),
            lead_thickness,
            standoff,
            lead_height,
            values.number("leads.foot_length"),
        ),
        centered_draft(
            "die-attach",
            "Die attach",
            StructureType.DIE_ATTACH,
            (die_length, die_width, attach),
            die_attach_z,
            "dieattach-84-1lmis",
            "group-die-attach",
            "Die attach",
        ),
        *pqfp_tie_bar_drafts(
            body_length,
            body_width,
            flag_length,
            flag_width,
            values.number("tie_bar.width"),
            flag_z,
            lead_thickness,
            (gap_x + gap_y) / 2,
        ),
    ]
    if values.boolean("thermal_land.enabled"):
        thickness = values.number("thermal_land.thickness")
        if standoff <= 0:
            raise ValueError("PQFP thermal land solder requires a positive standoff")
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
        materials=materials_for("pqfp"),
        power_w=values.number("die.power"),
        metadata={
            "lead_count": 2 * values.integer("leads.count_x") + 2 * values.integer("leads.count_y"),
            "reference_baseline": "FloTHERM PACK 2504 LQFP_32_7X7mm",
            "thermal_land_and_solder_enabled": values.boolean("thermal_land.enabled"),
        },
    )


def _validate(values: TemplateValues) -> None:
    package_length = values.number("package.length")
    package_width = values.number("package.width")
    body_length = values.number("body.length")
    body_width = values.number("body.width")
    if body_length > package_length or body_width > package_width:
        raise ValueError("PQFP body must fit inside the lead envelope")
    if max(values.number("flag.length"), values.number("die.length")) > body_length:
        raise ValueError("die and flag must fit inside the PQFP body")
    if max(values.number("flag.width"), values.number("die.width")) > body_width:
        raise ValueError("die and flag must fit inside the PQFP body")
    if values.number("leads.foot_length") <= values.number("leads.thickness"):
        raise ValueError("PQFP foot length must exceed lead thickness")
