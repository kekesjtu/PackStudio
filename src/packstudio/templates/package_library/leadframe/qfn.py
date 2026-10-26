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
from packstudio.templates.package_library.leadframe.qfn_primitives import (
    qfn_interconnect_drafts,
)
from packstudio.templates.package_library.leadframe.qfn_vias import qfn_vias


def definition() -> TemplateDefinition:
    fields = load_fields("qfn")
    return TemplateDefinition(
        id="qfn",
        display_name="QFN",
        category="Lead-frame packages",
        fields=fields,
        builder=_build,
        step_order=(
            "package_setup",
            "overall_package",
            "die",
            "lead_solder_interconnect",
            "dap",
            "bond_wires",
            "thermal_land",
            "thermal_vias",
        ),
        material_selections=load_material_selections("qfn", fields),
    )


def _build(values: TemplateValues, request: TemplateRequest) -> BuiltTemplate:
    length = values.number("package.length")
    width = values.number("package.width")
    standoff = values.number("package.standoff")
    pad_length = values.number("pad.length")
    pad_width = values.number("pad.width")
    pad_thickness = values.number("leads.thickness")
    exposed_pad_length = values.number("pad.exposed_length")
    exposed_pad_width = values.number("pad.exposed_width")
    exposed_pad_thickness = values.number("leads.exposed_thickness")
    die_length = values.number("die.length")
    die_width = values.number("die.width")
    attach = values.number("die.attach")
    die_thickness = values.number("die.thickness")
    die_attach_z = standoff + pad_thickness
    die_z = die_attach_z + attach
    die_top = die_z + die_thickness
    count_x = values.integer("leads.count_x")
    # A native two-sided preset leaves the absent side's count and pitch unfilled.
    count_y = 0 if values.is_missing("leads.count_y") else values.integer("leads.count_y")
    pitch_x = values.number("leads.pitch_x")
    pitch_y = values.number("leads.pitch_y") if count_y else 0
    lead_width = values.number("leads.width")
    _validate(values, length, width)
    span_x = (count_x - 1) * pitch_x + lead_width
    span_y = (count_y - 1) * pitch_y + lead_width
    diameter = values.number("bond_wire.diameter")
    wire_x_end = length / 2 - values.number("leads.length") - values.number("leads.etch")
    wire_y_end = width / 2 - values.number("leads.length") - values.number("leads.etch")

    drafts = [
        centered_draft(
            "encapsulant",
            "QFN encapsulant",
            StructureType.ENCAPSULANT,
            (length, width, values.number("encapsulant.thickness")),
            standoff,
            "eme-7730lf",
            "group-encapsulant",
            "Encapsulant",
            priority=100,
        ),
        centered_draft(
            "dap-upper",
            "Die attach pad",
            StructureType.EXPOSED_PAD,
            (pad_length, pad_width, pad_thickness - exposed_pad_thickness),
            standoff + exposed_pad_thickness,
            "leadframe-c194",
            "group-exposed-pad",
            "Exposed pad",
        ),
        centered_draft(
            "dap-exposed",
            "Exposed pad",
            StructureType.EXPOSED_PAD,
            (exposed_pad_length, exposed_pad_width, exposed_pad_thickness),
            standoff,
            "leadframe-c194",
            "group-exposed-pad",
            "Exposed pad",
        ),
        centered_draft(
            "center-solder",
            "Center solder",
            StructureType.SOLDER,
            (exposed_pad_length, exposed_pad_width, standoff),
            0,
            "solder-sn63",
            "group-solder",
            "Solder",
        ),
        centered_draft(
            "die-attach",
            "Die attach",
            StructureType.DIE_ATTACH,
            (die_length, die_width, attach),
            die_attach_z,
            "dieattach-2600bt",
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
        *four_direction_wire_drafts(
            "bond-wire",
            die_length,
            die_width,
            wire_x_end,
            wire_y_end,
            wire_x_end,
            wire_y_end,
            span_y,
            span_x,
            die_top - diameter,
            die_attach_z,
            die_top - die_attach_z,
            diameter,
            "qfn-bondwire-x",
            "qfn-bondwire-y",
            x_enabled=count_y > 0,
            y_enabled=count_x > 0,
        ),
        *qfn_interconnect_drafts(
            length,
            width,
            count_x,
            count_y,
            pitch_x,
            pitch_y,
            lead_width,
            values.number("leads.length"),
            values.number("leads.exposed_thickness"),
            values.number("leads.thickness"),
            values.number("leads.etch"),
            standoff,
        ),
    ]
    if values.boolean("thermal_land.enabled"):
        land = values.number("thermal_land.thickness")
        drafts.append(
            centered_draft(
                "thermal-land",
                "Thermal land",
                StructureType.EXPOSED_PAD,
                (exposed_pad_length, exposed_pad_width, land),
                -land,
                "leadframe-c194",
                "group-thermal-land",
                "Thermal land",
            )
        )
    via_drafts, via_materials = qfn_vias(values, request)
    return BuiltTemplate(
        drafts=[*drafts, *via_drafts],
        materials=[*materials_for("qfn"), *via_materials],
        power_w=values.number("die.power"),
        metadata={
            "lead_count": 2 * count_x + 2 * count_y,
            "reference_baseline": "FloTHERM PACK 2504 QFN_12X12_100",
            "thermal_land_enabled": values.boolean("thermal_land.enabled"),
            "thermal_vias_enabled": values.boolean("vias.enabled"),
        },
    )


def _validate(values: TemplateValues, length: float, width: float) -> None:
    count_y = 0 if values.is_missing("leads.count_y") else values.integer("leads.count_y")
    if values.integer("leads.count_x") + count_y == 0:
        raise ValueError("QFN must have leads on at least one pair of sides")
    if max(values.number("die.length"), values.number("pad.length")) > length:
        raise ValueError("die and DAP must fit inside the QFN body")
    if max(values.number("die.width"), values.number("pad.width")) > width:
        raise ValueError("die and DAP must fit inside the QFN body")
    if values.number("leads.exposed_thickness") >= values.number("leads.thickness"):
        raise ValueError("exposed lead thickness must be less than lead thickness")
    span_x = (values.integer("leads.count_x") - 1) * values.number("leads.pitch_x")
    span_y = (count_y - 1) * values.number("leads.pitch_y") if count_y else 0
    if span_x + values.number("leads.width") > length:
        raise ValueError("top/bottom QFN leads do not fit the package")
    if span_y + values.number("leads.width") > width:
        raise ValueError("left/right QFN leads do not fit the package")
