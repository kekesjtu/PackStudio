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
from packstudio.templates.package_library.core.primitives import (
    four_direction_wire_drafts,
    rectangular_ring_drafts,
)


def definition() -> TemplateDefinition:
    fields = load_fields("pbga_wb")
    return TemplateDefinition(
        id="pbga_wb",
        display_name="Wirebond PBGA",
        category="Ball grid arrays",
        fields=fields,
        builder=_build,
        step_order=(
            "package_setup",
            "package_substrate",
            "encapsulant",
            "die_flag_solder_mask",
            "die",
            "thermal_vias",
            "metal_layers",
            "solder_balls",
        ),
        material_selections=load_material_selections("pbga_wb", fields),
        has_bga=True,
    )


def _build(values: TemplateValues, request: TemplateRequest) -> BuiltTemplate:
    length = values.number("package.length")
    width = values.number("package.width")
    substrate = values.number("substrate.thickness")
    bga_height = values.number("bga.height")
    top_trace = values.number("trace.top_thickness")
    bottom_trace = values.number("trace.bottom_thickness")
    substrate_top = bga_height + substrate
    mask = values.number("solder_mask.thickness")
    die_length = values.number("die.length")
    die_width = values.number("die.width")
    attach = values.number("die.attach")
    die_z = substrate_top + mask + attach
    die_top = die_z + values.number("die.thickness")
    extent_length = values.number("bond_wire.extent_length")
    extent_width = values.number("bond_wire.extent_width")
    diameter = values.number("bond_wire.diameter")
    flag_length = values.number("flag.length")
    flag_width = values.number("flag.width")
    mold_length = values.number("encapsulant.length")
    mold_width = values.number("encapsulant.width")
    if mold_length > length or mold_width > width:
        raise ValueError("encapsulant must fit inside the substrate")
    if max(flag_length, die_length) > mold_length or max(flag_width, die_width) > mold_width:
        raise ValueError("die and flag must fit inside the encapsulant")
    if top_trace + bottom_trace >= substrate:
        raise ValueError("metal layers must be thinner than the substrate")

    drafts = [
        centered_draft(
            "encapsulant",
            "Encapsulant",
            StructureType.ENCAPSULANT,
            (mold_length, mold_width, values.number("encapsulant.thickness")),
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
            (die_length, die_width, values.number("die.thickness")),
            die_z,
            "silicon",
            "group-die",
            "Die",
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
        *rectangular_ring_drafts(
            "top-trace",
            length,
            width,
            extent_length - 2 * diameter,
            extent_width - 2 * diameter,
            substrate_top - top_trace,
            top_trace,
            StructureType.TRACE,
            "wirebond-trace-top",
            "group-traces",
            "Top traces",
        ),
        centered_draft(
            "bottom-trace",
            "Bottom trace",
            StructureType.TRACE,
            (length, width, bottom_trace),
            bga_height,
            "wirebond-trace-bottom",
            "group-traces",
            "Bottom trace",
        ),
        centered_draft(
            "die-flag",
            "Die flag",
            StructureType.LEAD_FRAME,
            (flag_length, flag_width, top_trace),
            substrate_top - top_trace,
            "wirebond-die-flag",
            "group-die-flag",
            "Die flag",
        ),
        centered_draft(
            "solder-mask-center",
            "Solder mask center",
            StructureType.SOLDER_MASK,
            (flag_length, flag_width, mask),
            substrate_top,
            "solder-mask",
            "group-solder-mask",
            "Solder mask",
        ),
        *rectangular_ring_drafts(
            "solder-mask-outer",
            length,
            width,
            extent_length + 0.1,
            extent_width + 0.1,
            substrate_top,
            mask,
            StructureType.SOLDER_MASK,
            "solder-mask",
            "group-solder-mask",
            "Solder mask",
        ),
        centered_draft(
            "die-attach",
            "Die attach",
            StructureType.DIE_ATTACH,
            (die_length, die_width, attach),
            substrate_top + mask,
            "ablestik-8510aa",
            "group-die-attach",
            "Die attach",
        ),
        *four_direction_wire_drafts(
            "bond-wire",
            die_length,
            die_width,
            extent_length / 2,
            extent_width / 2,
            extent_length / 2 - diameter,
            extent_width / 2 - diameter,
            die_width,
            die_length,
            die_top - diameter,
            substrate_top,
            die_top - diameter - substrate_top,
            diameter,
            "wirebond-bondwire-x",
            "wirebond-bondwire-y",
        ),
    ]
    if values.boolean("vias.enabled"):
        drafts.extend(
            via_grid_drafts(
                "thermal-via",
                values.integer("vias.rows"),
                values.integer("vias.columns"),
                values.number("vias.pitch"),
                sqrt(pi) * values.number("vias.diameter") / 2,
                bga_height + top_trace,
                substrate - top_trace - bottom_trace,
                material_id="wirebond-via",
            )
        )
    bga = build_bga_layer(
        values,
        request.bga or BgaConfiguration(),
        base_z=0,
        request=request,
    )
    return BuiltTemplate(
        drafts=drafts,
        blocks=bga.blocks,
        materials=[*materials_for("pbga_wb"), *bga.materials],
        group_names=bga.group_names,
        power_w=values.number("die.power"),
        metadata={
            **bga.metadata,
            "reference_baseline": "FloTHERM PACK 2504 PBGA_121_15X15mm",
        },
    )
