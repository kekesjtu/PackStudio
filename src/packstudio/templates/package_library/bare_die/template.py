from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.core.definitions import (
    TemplateDefinition,
    TemplateValues,
)
from packstudio.templates.package_library.core.fields import number, toggle
from packstudio.templates.package_library.core.generator import BuiltTemplate
from packstudio.templates.package_library.core.geometry import centered_draft
from packstudio.templates.package_library.core.material_options import DIE
from packstudio.templates.package_library.core.parameters import TemplateRequest


def definition() -> TemplateDefinition:
    return TemplateDefinition(
        id="bare_die",
        display_name="Bare Die",
        category="Bare die",
        fields=(
            number("die.length", "die", "芯片长度", 4.9, 0.2, 50),
            number("die.width", "die", "芯片宽度", 4.9, 0.2, 50),
            number("die.thickness", "die", "芯片厚度", 0.22, 0.03, 2),
            number("die.power", "die", "芯片功率", 2, 0, 1000, "W"),
            toggle("die.flipped", "options", "翻转芯片"),
        ),
        builder=_build,
        material_selections=(DIE,),
    )


def _build(values: TemplateValues, _request: TemplateRequest) -> BuiltTemplate:
    length = values.number("die.length")
    width = values.number("die.width")
    thickness = values.number("die.thickness")
    flipped = values.boolean("die.flipped")
    return BuiltTemplate(
        drafts=[
            centered_draft(
                "die",
                "Silicon die",
                StructureType.DIE,
                (length, width, thickness),
                0,
                "silicon",
                "group-die",
                "Die",
                metadata={"flipped": flipped},
            )
        ],
        power_w=values.number("die.power"),
        metadata={"flipped_die": flipped},
    )
