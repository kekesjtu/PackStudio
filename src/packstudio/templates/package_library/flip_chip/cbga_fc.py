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
        id="cbga_fc",
        display_name="Flip Chip CBGA",
        category="Ball grid arrays",
        fields=load_fields("cbga_fc"),
        builder=_build,
        step_order=(
            "package_setup",
            "package_substrate",
            "die",
            "flip_chip_bumps",
            "solder_balls",
            "top_cover",
        ),
        material_selections=load_material_selections("cbga_fc"),
        has_bga=True,
        has_flip_chip=True,
    )


def _build(values: TemplateValues, request: TemplateRequest) -> BuiltTemplate:
    return build(values, request, "alumina")
