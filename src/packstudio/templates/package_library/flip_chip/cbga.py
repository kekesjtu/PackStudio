from packstudio.templates.package_library.core.default_library import (
    load_fields,
    load_material_selections,
)
from packstudio.templates.package_library.core.definitions import (
    TemplateDefinition,
    TemplateValues,
)
from packstudio.templates.package_library.core.generator import BuiltTemplate
from packstudio.templates.package_library.core.parameters import TemplateRequest
from packstudio.templates.package_library.flip_chip.common import build


def definition() -> TemplateDefinition:
    return TemplateDefinition(
        id="flip_chip_cbga",
        display_name="Flip Chip CBGA",
        category="Ball grid arrays",
        fields=load_fields("flip_chip_cbga"),
        builder=_build,
        step_order=(
            "package_setup",
            "package_substrate",
            "die",
            "flip_chip_bumps",
            "solder_balls",
            "top_cover",
        ),
        material_selections=load_material_selections("flip_chip_cbga"),
        has_bga=True,
        has_flip_chip=True,
    )


def _build(values: TemplateValues, request: TemplateRequest) -> BuiltTemplate:
    return build(values, request, "alumina")
