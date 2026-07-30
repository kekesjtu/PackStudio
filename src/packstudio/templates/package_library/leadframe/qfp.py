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
from packstudio.templates.package_library.leadframe.fields import qfp_fields
from packstudio.templates.package_library.leadframe.qfp_primitives import (
    qfp_leadframe_drafts,
    qfp_tie_bar_drafts,
)


def definition() -> TemplateDefinition:
    return TemplateDefinition(
        id="qfp_family",
        display_name="QFP family",
        category="Lead-frame packages",
        fields=qfp_fields(),
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
                "group-lead-frame",
                "leadframe",
                "引线框材料",
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
                "group-tie-bar-plates",
                "leadframe",
                "Tie bar 填充材料",
                "epoxy-mold",
                ("epoxy-mold",),
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
    _validate(values)

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
            "qfp-die-flag",
            "group-die-flag",
            "Die flag",
        ),
        *four_direction_wire_drafts(
            "bond-wire",
            die_length,
            die_width,
            flag_length / 2 + gap_x,
            flag_width / 2 + gap_y,
            flag_length / 2 + gap_x,
            flag_width / 2 + gap_y,
            die_width,
            die_length,
            die_top - diameter,
            lead_z + lead_thickness,
            die_top - lead_z - lead_thickness,
            diameter,
            "qfp-bondwire-x",
            "qfp-bondwire-y",
        ),
        *qfp_leadframe_drafts(
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
        *qfp_tie_bar_drafts(
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
        materials=materials_for("qfp_family"),
        power_w=values.number("die.power"),
        metadata={
            "lead_count": 2 * values.integer("leads.count_x") + 2 * values.integer("leads.count_y"),
            "reference_baseline": "FloTHERM PACK 2504 LQFP_32_7X7mm",
            "exposed_pad_enabled": values.boolean("exposed_pad.enabled"),
        },
    )


def _validate(values: TemplateValues) -> None:
    package_length = values.number("package.length")
    package_width = values.number("package.width")
    body_length = values.number("body.length")
    body_width = values.number("body.width")
    if body_length > package_length or body_width > package_width:
        raise ValueError("QFP body must fit inside the lead envelope")
    if max(values.number("flag.length"), values.number("die.length")) > body_length:
        raise ValueError("die and flag must fit inside the QFP body")
    if max(values.number("flag.width"), values.number("die.width")) > body_width:
        raise ValueError("die and flag must fit inside the QFP body")
    if values.number("leads.foot_length") <= values.number("leads.thickness"):
        raise ValueError("QFP foot length must exceed lead thickness")
