from packstudio.templates.package_library.core.definitions import (
    TemplateDefinition,
    TemplateValues,
)
from packstudio.templates.package_library.core.generator import BuiltTemplate
from packstudio.templates.package_library.core.material_options import (
    DIE,
    selection,
)
from packstudio.templates.package_library.core.parameters import TemplateRequest
from packstudio.templates.package_library.flip_chip.common import build, fields
from packstudio.templates.package_library.flip_chip.cover_fields import material_selections


def definition() -> TemplateDefinition:
    return TemplateDefinition(
        id="flip_chip_pbga",
        display_name="Flip Chip PBGA",
        category="Ball grid arrays",
        fields=fields(),
        builder=_build,
        material_selections=(
            selection(
                "group-substrate",
                "substrate",
                "有机基板材料",
                "pbga-substrate",
                ("pbga-substrate", "bt"),
            ),
            DIE,
            *material_selections(),
        ),
        has_bga=True,
        has_flip_chip=True,
    )


def _build(values: TemplateValues, request: TemplateRequest) -> BuiltTemplate:
    return build(values, request, "pbga-substrate")
