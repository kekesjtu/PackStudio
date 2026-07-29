from functools import lru_cache
from typing import Any

from packstudio.domain.model import PackageModel
from packstudio.templates.package_library import (
    bare_die,
    fbga_fsbga,
    flip_chip_cbga,
    flip_chip_pbga,
    qfn,
    qfp_family,
    soic_family,
    wirebond_pbga,
)
from packstudio.templates.package_library.definitions import TemplateDefinition
from packstudio.templates.package_library.generator import generate_template
from packstudio.templates.package_library.parameters import TemplateRequest


@lru_cache(maxsize=1)
def definitions() -> dict[str, TemplateDefinition]:
    items = (
        flip_chip_cbga.definition(),
        flip_chip_pbga.definition(),
        wirebond_pbga.definition(),
        fbga_fsbga.definition(),
        qfn.definition(),
        qfp_family.definition(),
        soic_family.definition(),
        bare_die.definition(),
    )
    return {item.id: item for item in items}


def catalog() -> list[dict[str, Any]]:
    return [
        {
            "id": item.id,
            "display_name": item.display_name,
            "category": item.category,
            "has_bga": item.has_bga,
            "bga_representations": (["equivalent", "discrete"] if item.has_bga else []),
            "implementation_status": "packstudio_native",
            "runtime_reference_data_required": False,
        }
        for item in definitions().values()
    ]


def definition(template_id: str) -> TemplateDefinition:
    try:
        return definitions()[template_id]
    except KeyError as error:
        raise ValueError(f"unknown template {template_id}") from error


def schema(template_id: str) -> dict[str, Any]:
    return definition(template_id).schema()


def default_request(template_id: str) -> TemplateRequest:
    item = definition(template_id)
    return TemplateRequest(
        template_id=template_id,
        design_name=item.display_name,
        bga={} if item.has_bga else None,
    )


def generate(request: TemplateRequest) -> PackageModel:
    return generate_template(definition(request.template_id), request)
