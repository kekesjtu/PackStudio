from math import pi

from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.bga.layers import build_bga_layer
from packstudio.templates.package_library.core.definitions import (
    FieldDefinition,
    TemplateValues,
)
from packstudio.templates.package_library.core.fields import integer, number
from packstudio.templates.package_library.core.generator import BuiltTemplate
from packstudio.templates.package_library.core.geometry import DraftBlock, centered_draft
from packstudio.templates.package_library.core.parameters import (
    BgaConfiguration,
    TemplateRequest,
)
from packstudio.templates.package_library.flip_chip.cover import append_top_structure
from packstudio.templates.package_library.flip_chip.cover_fields import fields as cover_fields
from packstudio.templates.package_library.flip_chip.layers import build_flip_chip_layer


def fields(footprint_field: FieldDefinition) -> tuple[FieldDefinition, ...]:
    return (
        footprint_field,
        number("substrate.length", "package_substrate", "基板长度 D", 6, 2, 50),
        number("substrate.width", "package_substrate", "基板宽度 E", 6, 2, 50),
        number("substrate.thickness", "package_substrate", "基板厚度 A2", 1.15, 0.1, 5),
        number("die.length", "die", "芯片长度", 1.8, 0.2, 40),
        number("die.width", "die", "芯片宽度", 1.8, 0.2, 40),
        number("die.thickness", "die", "芯片厚度", 0.61, 0.03, 2),
        number("die.power", "die", "芯片功率", 0, 0, 1000, "W"),
        integer("bumps.total", "flip_chip_bumps", "凸点总数", 49, 1, 10000),
        number("bumps.diameter", "flip_chip_bumps", "凸点直径", 0.12, 0.01, 0.5),
        number("bumps.height", "flip_chip_bumps", "凸点层厚度", 0.1, 0.01, 0.5),
        integer("bga.columns", "solder_balls", "X 方向焊球数 MD", 7, 1, 50),
        integer("bga.rows", "solder_balls", "Y 方向焊球数 ME", 7, 1, 50),
        number("bga.pitch", "solder_balls", "焊球间距 e", 0.8, 0.2, 2),
        number("bga.diameter", "solder_balls", "焊球直径 b", 0.5, 0.05, 1.5),
        number("bga.height", "solder_balls", "基板离板高度 A1", 0.4, 0.05, 1.5),
        *cover_fields(),
    )


def build(
    values: TemplateValues,
    request: TemplateRequest,
    substrate_material: str,
) -> BuiltTemplate:
    substrate_length = values.number("substrate.length")
    substrate_width = values.number("substrate.width")
    substrate_thickness = values.number("substrate.thickness")
    bga_height = values.number("bga.height")
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
            bga_height,
            substrate_material,
            "group-substrate",
            "Substrate",
        )
    ]
    flip = build_flip_chip_layer(
        values,
        die_length,
        die_width,
        bga_height + substrate_thickness,
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
    die_z = bga_height + substrate_thickness + bump_height
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
    append_top_structure(
        drafts,
        values,
        die_length,
        die_width,
        bga_height + substrate_thickness,
        die_z + die_thickness,
    )
    bga = build_bga_layer(
        values,
        request.bga or BgaConfiguration(),
        substrate_length,
        substrate_width,
        base_z=0,
    )
    return BuiltTemplate(
        drafts=drafts,
        blocks=bga.blocks,
        materials=[*flip.materials, *bga.materials],
        group_names=bga.group_names,
        power_w=values.number("die.power"),
        metadata={**flip.metadata, **bga.metadata},
    )
