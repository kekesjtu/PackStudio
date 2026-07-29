from math import pi

from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.definitions import (
    FieldDefinition,
    TemplateValues,
)
from packstudio.templates.package_library.fields import choice, integer, number
from packstudio.templates.package_library.generator import BuiltTemplate
from packstudio.templates.package_library.geometry import DraftBlock, centered_draft
from packstudio.templates.package_library.layers import (
    build_bga_layer,
    build_flip_chip_layer,
)
from packstudio.templates.package_library.parameters import (
    BgaConfiguration,
    TemplateRequest,
)


def fields() -> tuple[FieldDefinition, ...]:
    return (
        number("substrate.length", "substrate", "基板长度", 6, 2, 50),
        number("substrate.width", "substrate", "基板宽度", 6, 2, 50),
        number("substrate.thickness", "substrate", "基板厚度", 1.15, 0.1, 5),
        number("die.length", "die", "芯片长度", 1.8, 0.2, 40),
        number("die.width", "die", "芯片宽度", 1.8, 0.2, 40),
        number("die.thickness", "die", "芯片厚度", 0.61, 0.03, 2),
        number("die.power", "die", "芯片功率", 0, 0, 1000, "W"),
        integer("bumps.total", "interconnect", "凸点总数", 49, 1, 10000),
        number("bumps.diameter", "interconnect", "凸点直径", 0.12, 0.01, 0.5),
        number("bumps.height", "interconnect", "凸点层厚度", 0.1, 0.01, 0.5),
        integer("bga.columns", "interconnect", "BGA X 方向数量", 7, 1, 50),
        integer("bga.rows", "interconnect", "BGA Y 方向数量", 7, 1, 50),
        number("bga.pitch", "interconnect", "BGA 间距", 0.8, 0.2, 2),
        number("bga.diameter", "interconnect", "焊球直径", 0.5, 0.05, 1.5),
        number("bga.height", "interconnect", "焊球层高度", 0.4, 0.05, 1.5),
        choice(
            "cover.type",
            "encapsulant",
            "顶部结构",
            "bare_die",
            ("bare_die", "encapsulant", "lid"),
        ),
        number(
            "cover.thickness",
            "encapsulant",
            "塑封顶部厚度",
            0.3,
            0.05,
            3,
            visible_when={"cover.type": "encapsulant"},
        ),
        number(
            "lid.tim_thickness",
            "encapsulant",
            "TIM 厚度",
            0.05,
            0.01,
            1,
            visible_when={"cover.type": "lid"},
        ),
        number(
            "lid.thickness",
            "encapsulant",
            "顶盖厚度",
            0.3,
            0.05,
            3,
            visible_when={"cover.type": "lid"},
        ),
    )


def build(
    values: TemplateValues,
    request: TemplateRequest,
    substrate_material: str,
) -> BuiltTemplate:
    substrate_length = values.number("substrate.length")
    substrate_width = values.number("substrate.width")
    substrate_thickness = values.number("substrate.thickness")
    die_length = values.number("die.length")
    die_width = values.number("die.width")
    die_thickness = values.number("die.thickness")
    bump_height = values.number("bumps.height")
    if die_length > substrate_length or die_width > substrate_width:
        raise ValueError("die must fit inside the substrate")
    bump_area = values.integer("bumps.total") * pi * (values.number("bumps.diameter") / 2) ** 2
    if bump_area >= die_length * die_width:
        raise ValueError("flip-chip bump fill fraction must be below one")

    drafts = [
        centered_draft(
            "substrate",
            "Package substrate",
            StructureType.SUBSTRATE,
            (substrate_length, substrate_width, substrate_thickness),
            0,
            substrate_material,
            "group-substrate",
            "Substrate",
        )
    ]
    flip = build_flip_chip_layer(
        values,
        die_length,
        die_width,
        substrate_thickness,
    )
    bump = flip.blocks[0]
    drafts.append(
        DraftBlock(
            id=bump.id,
            name=bump.name,
            structure_type=bump.structure_type,
            origin=(bump.origin.x, bump.origin.y, bump.origin.z),
            size=(bump.size.x, bump.size.y, bump.size.z),
            material_id=bump.material_id,
            group_id=bump.parent_group_id,
            group_name=flip.group_names[bump.parent_group_id],
            metadata=bump.metadata,
        )
    )
    die_z = substrate_thickness + bump_height
    drafts.append(
        centered_draft(
            "die",
            "Silicon die",
            StructureType.DIE,
            (die_length, die_width, die_thickness),
            die_z,
            "silicon",
            "group-die",
            "Die",
        )
    )
    _append_top_structure(drafts, values, substrate_length, substrate_width, die_z + die_thickness)
    bga = build_bga_layer(
        values,
        request.bga or BgaConfiguration(),
        substrate_length,
        substrate_width,
    )
    return BuiltTemplate(
        drafts=drafts,
        blocks=bga.blocks,
        materials=[*flip.materials, *bga.materials],
        group_names=bga.group_names,
        power_w=values.number("die.power"),
        metadata={**flip.metadata, **bga.metadata},
    )


def _append_top_structure(
    drafts: list[DraftBlock],
    values: TemplateValues,
    package_length: float,
    package_width: float,
    die_top: float,
) -> None:
    cover_type = values.text("cover.type")
    if cover_type == "encapsulant":
        thickness = values.number("cover.thickness")
        drafts.append(
            centered_draft(
                "encapsulant",
                "Encapsulant",
                StructureType.ENCAPSULANT,
                (package_length, package_width, die_top + thickness),
                0,
                "epoxy-mold",
                "group-encapsulant",
                "Encapsulant",
                priority=100,
            )
        )
    elif cover_type == "lid":
        tim = values.number("lid.tim_thickness")
        lid = values.number("lid.thickness")
        drafts.extend(
            [
                centered_draft(
                    "lid-tim",
                    "Thermal interface",
                    StructureType.THERMAL_INTERFACE,
                    (package_length * 0.8, package_width * 0.8, tim),
                    die_top,
                    "tim",
                    "group-top",
                    "Top structures",
                ),
                centered_draft(
                    "lid",
                    "Copper lid",
                    StructureType.LID,
                    (package_length, package_width, lid),
                    die_top + tim,
                    "lid-copper",
                    "group-top",
                    "Top structures",
                ),
            ]
        )
