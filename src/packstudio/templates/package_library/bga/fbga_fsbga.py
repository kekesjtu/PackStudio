from math import pi, sqrt

from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.bga.footprints import fbga_footprint_field
from packstudio.templates.package_library.bga.layers import build_bga_layer
from packstudio.templates.package_library.bga.primitives import via_grid_drafts
from packstudio.templates.package_library.core.baseline_materials import materials_for
from packstudio.templates.package_library.core.definitions import (
    TemplateDefinition,
    TemplateValues,
)
from packstudio.templates.package_library.core.fields import integer, number, toggle
from packstudio.templates.package_library.core.generator import BuiltTemplate
from packstudio.templates.package_library.core.geometry import centered_draft
from packstudio.templates.package_library.core.material_options import (
    BOND_WIRES,
    DIE,
    ENCAPSULANT,
    selection,
)
from packstudio.templates.package_library.core.parameters import (
    BgaConfiguration,
    TemplateRequest,
)
from packstudio.templates.package_library.core.primitives import four_direction_wire_drafts


def definition() -> TemplateDefinition:
    return TemplateDefinition(
        id="fbga_fsbga",
        display_name="FBGA / FSBGA",
        category="Ball grid arrays",
        fields=(
            fbga_footprint_field(),
            number("package.length", "overall_package", "封装长度 D", 4, 2, 30),
            number("package.width", "overall_package", "封装宽度 E", 4, 2, 30),
            number(
                "substrate.thickness",
                "overall_package",
                "基板厚度 A2",
                0.36,
                0.1,
                3,
            ),
            number(
                "trace.top_thickness",
                "metal_layers",
                "顶部金属层厚度",
                0.018,
                0.001,
                0.2,
            ),
            number(
                "trace.bottom_thickness",
                "metal_layers",
                "底部金属层厚度",
                0.018,
                0.001,
                0.2,
            ),
            number("die.length", "die", "芯片长度", 1.2, 0.2, 20),
            number("die.width", "die", "芯片宽度", 1.2, 0.2, 20),
            number("die.thickness", "die", "芯片厚度", 0.3, 0.03, 1.5),
            number("die.attach", "die", "粘接层厚度", 0.025, 0.005, 0.3),
            number("die.power", "die", "芯片功率", 0, 0, 1000, "W"),
            number("encapsulant.thickness", "encapsulant", "塑封厚度", 0.65, 0.1, 5),
            number("solder_mask.thickness", "encapsulant", "阻焊层厚度", 0.05, 0.005, 0.3),
            number("bond_wire.extent_length", "bond_wires", "键合焊盘长度范围", 2, 0.3, 20),
            number("bond_wire.extent_width", "bond_wires", "键合焊盘宽度范围", 2, 0.3, 20),
            number("bond_wire.diameter", "bond_wires", "键合线等效宽度", 0.025, 0.01, 0.2),
            toggle("vias.enabled", "thermal_vias", "包含热通孔", True),
            number(
                "vias.diameter",
                "thermal_vias",
                "通孔直径",
                0.2,
                0.02,
                1,
                visible_when={"vias.enabled": True},
            ),
            number(
                "vias.plating",
                "thermal_vias",
                "通孔镀层厚度",
                0.025,
                0.001,
                0.2,
                visible_when={"vias.enabled": True},
            ),
            number(
                "vias.offset_x",
                "thermal_vias",
                "通孔 X 偏移",
                0.4,
                -3,
                3,
                visible_when={"vias.enabled": True},
            ),
            number(
                "vias.offset_y",
                "thermal_vias",
                "通孔 Y 偏移",
                0.4,
                -3,
                3,
                visible_when={"vias.enabled": True},
            ),
            integer("bga.columns", "solder_balls", "X 方向焊球数 MD", 5, 1, 50),
            integer("bga.rows", "solder_balls", "Y 方向焊球数 ME", 5, 1, 50),
            number("bga.pitch", "solder_balls", "焊球间距 e", 0.8, 0.2, 2),
            number("bga.diameter", "solder_balls", "焊球直径 b", 0.46, 0.05, 1.5),
            number("bga.height", "solder_balls", "基板离板高度 A1", 0.4, 0.05, 1.5),
        ),
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
        material_selections=(
            selection("group-substrate", "overall_package", "基板材料", "bt", ("bt",)),
            DIE,
            selection(
                "group-die-attach",
                "die",
                "芯片粘接材料",
                "qmi-595",
                ("qmi-595",),
            ),
            ENCAPSULANT,
            BOND_WIRES,
            selection(
                "group-solder-mask",
                "encapsulant",
                "阻焊层材料",
                "solder-mask",
                ("solder-mask",),
            ),
        ),
        has_bga=True,
        default_bga_representation="discrete",
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
            "fbga-trace-top",
            "group-traces",
            "Dielectric & traces",
        ),
        centered_draft(
            "trace-bottom",
            "Bottom trace",
            StructureType.TRACE,
            (length, width, bottom_trace),
            bga_height,
            "fbga-trace-bottom",
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
            "fbga-bondwire-x",
            "fbga-bondwire-y",
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
                material_id="fbga-via",
            )
        )
    bga = build_bga_layer(
        values,
        request.bga or BgaConfiguration(representation="discrete"),
        length,
        width,
        base_z=0,
    )
    return BuiltTemplate(
        drafts=drafts,
        blocks=bga.blocks,
        materials=[*materials_for("fbga_fsbga"), *bga.materials],
        group_names=bga.group_names,
        power_w=values.number("die.power"),
        metadata={
            **bga.metadata,
            "reference_baseline": "FloTHERM PACK 2504 ChipArray_24_4X4mm_0_8",
        },
    )
