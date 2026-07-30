from functools import lru_cache
from typing import Any

from packstudio.domain.model import PackageModel
from packstudio.templates.package_library.bare_die import template as bare_die
from packstudio.templates.package_library.bga import fbga_fsbga, wirebond_pbga
from packstudio.templates.package_library.core.definitions import TemplateDefinition
from packstudio.templates.package_library.core.generator import generate_template
from packstudio.templates.package_library.core.parameters import TemplateRequest
from packstudio.templates.package_library.flip_chip import (
    cbga as flip_chip_cbga,
)
from packstudio.templates.package_library.flip_chip import (
    pbga as flip_chip_pbga,
)
from packstudio.templates.package_library.leadframe import (
    qfn,
)
from packstudio.templates.package_library.leadframe import (
    qfp as qfp_family,
)
from packstudio.templates.package_library.leadframe import (
    soic as soic_family,
)


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
        bga={"representation": item.default_bga_representation} if item.has_bga else None,
    )


def generate(request: TemplateRequest) -> PackageModel:
    return generate_template(definition(request.template_id), request)
