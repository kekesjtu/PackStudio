from packstudio.templates.package_library.definitions import (
    TemplateDefinition,
    TemplateValues,
)
from packstudio.templates.package_library.flip_common import build, fields
from packstudio.templates.package_library.generator import BuiltTemplate
from packstudio.templates.package_library.parameters import TemplateRequest


def definition() -> TemplateDefinition:
    return TemplateDefinition(
        id="flip_chip_cbga",
        display_name="Flip Chip CBGA",
        category="Ball grid arrays",
        fields=fields(),
        builder=_build,
        has_bga=True,
        has_flip_chip=True,
    )


def _build(values: TemplateValues, request: TemplateRequest) -> BuiltTemplate:
    return build(values, request, "alumina")
