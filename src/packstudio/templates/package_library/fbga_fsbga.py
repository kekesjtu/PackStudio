from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.definitions import (
    TemplateDefinition,
    TemplateValues,
)
from packstudio.templates.package_library.fields import integer, number, toggle
from packstudio.templates.package_library.generator import BuiltTemplate
from packstudio.templates.package_library.geometry import centered_draft
from packstudio.templates.package_library.layers import build_bga_layer
from packstudio.templates.package_library.parameters import (
    BgaConfiguration,
    TemplateRequest,
)
from packstudio.templates.package_library.primitives import (
    bond_wire_drafts,
    via_grid_drafts,
)


def definition() -> TemplateDefinition:
    return TemplateDefinition(
        id="fbga_fsbga",
        display_name="FBGA / FSBGA",
        category="Ball grid arrays",
        fields=(
            number("package.length", "package", "封装长度", 4, 2, 30),
            number("package.width", "package", "封装宽度", 4, 2, 30),
            number("substrate.thickness", "substrate", "基板厚度", 0.36, 0.1, 3),
            number("die.length", "die", "芯片长度", 1.2, 0.2, 20),
            number("die.width", "die", "芯片宽度", 1.2, 0.2, 20),
            number("die.thickness", "die", "芯片厚度", 0.3, 0.03, 1.5),
            number("die.attach", "die", "粘接层厚度", 0.025, 0.005, 0.3),
            number("die.power", "die", "芯片功率", 0, 0, 1000, "W"),
            number("encapsulant.thickness", "encapsulant", "塑封厚度", 0.65, 0.1, 5),
            number("bond_wire.diameter", "bond_wires", "键合线等效宽度", 0.025, 0.01, 0.2),
            toggle("vias.enabled", "interconnect", "包含热通孔", True),
            integer(
                "vias.columns",
                "interconnect",
                "通孔 X 方向数量",
                5,
                1,
                20,
                visible_when={"vias.enabled": True},
            ),
            integer(
                "vias.rows",
                "interconnect",
                "通孔 Y 方向数量",
                5,
                1,
                20,
                visible_when={"vias.enabled": True},
            ),
            number(
                "vias.pitch",
                "interconnect",
                "通孔间距",
                0.8,
                0.1,
                3,
                visible_when={"vias.enabled": True},
            ),
            number(
                "vias.diameter",
                "interconnect",
                "通孔等效边长",
                0.177245,
                0.02,
                1,
                visible_when={"vias.enabled": True},
            ),
            integer("bga.columns", "interconnect", "BGA X 方向数量", 5, 1, 50),
            integer("bga.rows", "interconnect", "BGA Y 方向数量", 5, 1, 50),
            number("bga.pitch", "interconnect", "BGA 间距", 0.8, 0.2, 2),
            number("bga.diameter", "interconnect", "焊球直径", 0.46, 0.05, 1.5),
            number("bga.height", "interconnect", "焊球层高度", 0.4, 0.05, 1.5),
        ),
        builder=_build,
        has_bga=True,
    )


def _build(values: TemplateValues, request: TemplateRequest) -> BuiltTemplate:
    length = values.number("package.length")
    width = values.number("package.width")
    substrate = values.number("substrate.thickness")
    die_length = values.number("die.length")
    die_width = values.number("die.width")
    die_thickness = values.number("die.thickness")
    attach = values.number("die.attach")
    if die_length > length or die_width > width:
        raise ValueError("die must fit inside the substrate")
    trace = min(0.018, substrate / 4)
    mask = 0.05
    die_z = substrate + mask + attach
    drafts = [
        centered_draft(
            "substrate",
            "BT substrate",
            StructureType.SUBSTRATE,
            (length, width, substrate),
            0,
            "bt",
            "group-substrate",
            "Substrate",
            priority=100,
        ),
        centered_draft(
            "bottom-trace",
            "Bottom copper trace",
            StructureType.TRACE,
            (length, width, trace),
            0,
            "copper",
            "group-traces",
            "Metal layers",
        ),
        centered_draft(
            "top-trace",
            "Top copper trace",
            StructureType.TRACE,
            (length, width, trace),
            substrate - trace,
            "copper",
            "group-traces",
            "Metal layers",
        ),
        centered_draft(
            "solder-mask",
            "Top solder mask",
            StructureType.SOLDER_MASK,
            (length, width, mask),
            substrate,
            "solder-mask",
            "group-solder-mask",
            "Solder mask",
        ),
        centered_draft(
            "die-attach",
            "Die attach",
            StructureType.DIE_ATTACH,
            (die_length, die_width, attach),
            substrate + mask,
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
        centered_draft(
            "encapsulant",
            "Epoxy encapsulant",
            StructureType.ENCAPSULANT,
            (length, width, values.number("encapsulant.thickness")),
            substrate,
            "epoxy-mold",
            "group-encapsulant",
            "Encapsulant",
            priority=100,
        ),
        *bond_wire_drafts(
            "bond-wire",
            die_length,
            die_width,
            min(length, die_length + 2),
            min(width, die_width + 2),
            die_z + die_thickness,
            values.number("bond_wire.diameter"),
        ),
    ]
    if values.boolean("vias.enabled"):
        via_height = max(substrate - 2 * trace, 0.01)
        drafts.extend(
            via_grid_drafts(
                "via",
                values.integer("vias.rows"),
                values.integer("vias.columns"),
                values.number("vias.pitch"),
                values.number("vias.diameter"),
                trace,
                via_height,
            )
        )
    bga = build_bga_layer(
        values,
        request.bga or BgaConfiguration(),
        length,
        width,
    )
    return BuiltTemplate(
        drafts=drafts,
        blocks=bga.blocks,
        materials=bga.materials,
        group_names=bga.group_names,
        power_w=values.number("die.power"),
        metadata=bga.metadata,
    )
