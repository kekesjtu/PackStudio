from math import pi, sqrt

from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.bga.layers import build_bga_layer
from packstudio.templates.package_library.bga.primitives import via_grid_drafts
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
from packstudio.templates.package_library.core.parameters import (
    BgaConfiguration,
    TemplateRequest,
)
from packstudio.templates.package_library.core.primitives import four_direction_wire_drafts


def definition() -> TemplateDefinition:
    fields = load_fields("chip_array")
    return TemplateDefinition(
        id="chip_array",
        display_name="Chip Array",
        category="Ball grid arrays",
        fields=fields,
        builder=_build,
        step_order=(
            "package_setup",
            "overall_package",
            "die",
            "encapsulant",
            "bond_wires",
            "thermal_vias",
            "metal_layers",
            "solder_balls",
        ),
        material_selections=load_material_selections("chip_array", fields),
        has_bga=True,
    )


def _build(values: TemplateValues, request: TemplateRequest) -> BuiltTemplate:
    length = values.number("package.length")
    width = values.number("package.width")
    substrate = values.number("substrate.thickness")
    bga_height = values.number("bga.height")
    top_trace = values.number("trace.top_thickness")
    bottom_trace = values.number("trace.bottom_thickness")
    mask = values.number("solder_mask.thickness")
    die_length = values.number("die.length")
    die_width = values.number("die.width")
    die_thickness = values.number("die.thickness")
    attach = values.number("die.attach")
    substrate_top = bga_height + substrate
    die_z = substrate_top + mask
    die_top = die_z + die_thickness
    if die_length > length or die_width > width:
        raise ValueError("die must fit inside the substrate")
    if top_trace + bottom_trace >= substrate:
        raise ValueError("metal layers must be thinner than the substrate")

    drafts = [
        centered_draft(
            "encapsulant",
            "Encapsulant",
            StructureType.ENCAPSULANT,
            (length, width, values.number("encapsulant.thickness")),
            substrate_top,
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
            "solder-mask",
            "Solder mask",
            StructureType.SOLDER_MASK,
            (die_length, die_width, mask),
            substrate_top,
            "solder-mask",
            "group-solder-mask",
            "Solder mask",
        ),
        centered_draft(
            "dielectric",
            "BT dielectric",
            StructureType.SUBSTRATE,
            (length, width, substrate),
            bga_height,
            "bt",
            "group-substrate",
            "Dielectric & traces",
            priority=100,
        ),
        centered_draft(
            "trace-top",
            "Top trace",
            StructureType.TRACE,
            (length, width, top_trace),
            substrate_top - top_trace,
            "chip-array-trace-top",
            "group-traces",
            "Dielectric & traces",
        ),
        centered_draft(
            "trace-bottom",
            "Bottom trace",
            StructureType.TRACE,
            (length, width, bottom_trace),
            bga_height,
            "chip-array-trace-bottom",
            "group-traces",
            "Dielectric & traces",
        ),
        centered_draft(
            "die-attach",
            "Die attach",
            StructureType.DIE_ATTACH,
            (die_length, die_width, attach),
            die_z,
            "qmi-595",
            "group-die-attach",
            "Die attach",
        ),
        *four_direction_wire_drafts(
            "bond-wire",
            die_length,
            die_width,
            values.number("bond_wire.extent_length") / 2 - values.number("bond_wire.diameter"),
            values.number("bond_wire.extent_width") / 2 - values.number("bond_wire.diameter"),
            values.number("bond_wire.extent_length") / 2 - values.number("bond_wire.diameter"),
            values.number("bond_wire.extent_width") / 2 - values.number("bond_wire.diameter"),
            die_width,
            die_length,
            die_top - values.number("bond_wire.diameter"),
            substrate_top,
            die_top - substrate_top,
            values.number("bond_wire.diameter"),
            "chip-array-bondwire-x",
            "chip-array-bondwire-y",
        ),
    ]
    if values.boolean("vias.enabled"):
        via_side = sqrt(pi) * values.number("vias.diameter") / 2
        drafts.extend(
            via_grid_drafts(
                "thermal-via",
                values.integer("bga.rows"),
                values.integer("bga.columns"),
                values.number("bga.pitch"),
                via_side,
                bga_height + bottom_trace,
                substrate - top_trace - bottom_trace,
                center_x=values.number("vias.offset_x"),
                center_y=values.number("vias.offset_y"),
                material_id="chip-array-via",
            )
        )
    bga = build_bga_layer(
        values,
        request.bga or BgaConfiguration(representation="discrete"),
        base_z=0,
    )
    return BuiltTemplate(
        drafts=drafts,
        blocks=bga.blocks,
        materials=[*materials_for("chip_array"), *bga.materials],
        group_names=bga.group_names,
        power_w=values.number("die.power"),
        metadata={
            **bga.metadata,
            "reference_baseline": "FloTHERM PACK 2504 ChipArray_24_4X4mm_0_8",
        },
    )
