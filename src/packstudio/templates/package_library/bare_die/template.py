from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.bare_die.footprints import bare_die_footprint_field
from packstudio.templates.package_library.core.definitions import (
    FieldDefinition,
    TemplateDefinition,
    TemplateValues,
)
from packstudio.templates.package_library.core.fields import integer, number, toggle
from packstudio.templates.package_library.core.generator import BuiltTemplate
from packstudio.templates.package_library.core.geometry import centered_draft
from packstudio.templates.package_library.core.material_options import DIE
from packstudio.templates.package_library.core.parameters import TemplateRequest
from packstudio.templates.package_library.flip_chip.layers import build_flip_chip_layer


def definition() -> TemplateDefinition:
    return TemplateDefinition(
        id="bare_die",
        display_name="Bare Die",
        category="Bare die",
        fields=_fields(),
        builder=_build,
        step_order=("package_setup", "die", "bumped_die"),
        material_selections=(DIE,),
        has_flip_chip=True,
    )


def _fields() -> tuple[FieldDefinition, ...]:
    return (
        bare_die_footprint_field(),
        number("die.length", "die", "芯片长度", 4.9, 0.2, 50),
        number("die.width", "die", "芯片宽度", 4.9, 0.2, 50),
        number("die.thickness", "die", "芯片厚度", 0.22, 0.03, 2),
        number("die.power", "die", "芯片功率", 2, 0, 1000, "W"),
        toggle("die.flipped", "die", "翻转芯片"),
        toggle("bumps.enabled", "bumped_die", "包含凸点与底填充"),
        integer(
            "bumps.total",
            "bumped_die",
            "凸点总数",
            100,
            1,
            10000,
            visible_when={"bumps.enabled": True},
        ),
        number(
            "bumps.diameter",
            "bumped_die",
            "凸点直径",
            0.12,
            0.01,
            0.5,
            visible_when={"bumps.enabled": True},
        ),
        number(
            "bumps.height",
            "bumped_die",
            "凸点层厚度",
            0.1,
            0.01,
            0.5,
            visible_when={"bumps.enabled": True},
        ),
    )


def _build(values: TemplateValues, _request: TemplateRequest) -> BuiltTemplate:
    length = values.number("die.length")
    width = values.number("die.width")
    thickness = values.number("die.thickness")
    flipped = values.boolean("die.flipped")
    bumped = values.boolean("bumps.enabled")
    bump_layer = build_flip_chip_layer(values, length, width, 0) if bumped else None
    die_z = values.number("bumps.height") if bumped else 0
    return BuiltTemplate(
        drafts=[
            centered_draft(
                "die",
                "Silicon die",
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
