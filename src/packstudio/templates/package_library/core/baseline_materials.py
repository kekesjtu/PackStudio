from packstudio.domain.materials import Material
from packstudio.templates.package_library.core.default_library import template_defaults


def materials_for(template_id: str) -> list[Material]:
    return [
        Material.model_validate(item)
        for item in template_defaults(template_id)["baseline_materials"]
    ]
