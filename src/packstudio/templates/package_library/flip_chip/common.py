from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.bga.layers import build_bga_layer
from packstudio.templates.package_library.core.definitions import (
    TemplateValues,
)
from packstudio.templates.package_library.core.generator import BuiltTemplate
from packstudio.templates.package_library.core.geometry import DraftBlock, centered_draft
from packstudio.templates.package_library.core.parameters import (
    BgaConfiguration,
    TemplateRequest,
)
from packstudio.templates.package_library.flip_chip.cover import append_top_structure
from packstudio.templates.package_library.flip_chip.layers import build_flip_chip_layer
from packstudio.templates.package_library.flip_chip.slug import append_slug


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
        request=request,
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
    append_slug(drafts, values, bga_height + substrate_thickness)
    bga = build_bga_layer(
        values,
        request.bga or BgaConfiguration(),
        base_z=0,
        request=request,
    )
    substrate_materials = []
    if request.template_id == "pbga_fc":
        from packstudio.templates.package_library.flip_chip.substrate import append_substrate

        substrate_materials = append_substrate(drafts, values, request)
    return BuiltTemplate(
        drafts=drafts,
        blocks=bga.blocks,
        materials=[*flip.materials, *bga.materials, *substrate_materials],
        group_names=bga.group_names,
        power_w=values.number("die.power"),
        metadata={**flip.metadata, **bga.metadata},
    )
