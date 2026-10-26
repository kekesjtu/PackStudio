from packstudio.domain.enums import StructureType
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
from packstudio.templates.package_library.core.materials import material
from packstudio.templates.package_library.core.parameters import TemplateRequest
from packstudio.templates.package_library.flip_chip.layers import build_flip_chip_layer


def definition() -> TemplateDefinition:
    fields = load_fields("bare_die")
    return TemplateDefinition(
        id="bare_die",
        display_name="Bare Die",
        category="Bare die",
        fields=fields,
        builder=_build,
        step_order=("die", "bumped_die"),
        material_selections=load_material_selections("bare_die", fields),
        has_flip_chip=True,
    )


def _build(values: TemplateValues, request: TemplateRequest) -> BuiltTemplate:
    length = values.number("die.length")
    width = values.number("die.width")
    thickness = values.number("die.thickness")
    flipped = values.boolean("die.flipped")
    bumped = values.boolean("bumps.enabled")
    bump_layer = (
        build_flip_chip_layer(values, length, width, 0, request=request) if bumped else None
    )
    die_z = values.number("bumps.height") if bumped else 0
    die_material = material(request.material_assignments["group-die"], request.custom_materials)
    return BuiltTemplate(
        drafts=[
            centered_draft(
                "die",
                f"{die_material.name.removesuffix(' (Pure)')} die",
                StructureType.DIE,
                (length, width, thickness),
                die_z,
                "silicon",
                "group-die",
                "Die",
                metadata={"flipped": flipped},
            )
        ],
        blocks=[] if bump_layer is None else bump_layer.blocks,
        materials=[] if bump_layer is None else bump_layer.materials,
        group_names={} if bump_layer is None else bump_layer.group_names,
        power_w=values.number("die.power"),
        metadata={
            "flipped_die": flipped,
            "bumped_die": bumped,
            "bump_representation": ("thick_orthotropic_equivalent" if bumped else "not_present"),
            **({} if bump_layer is None else bump_layer.metadata),
        },
    )
