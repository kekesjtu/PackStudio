from functools import lru_cache
from threading import Lock
from typing import Any

from packstudio.domain.model import PackageModel
from packstudio.templates.package_library.bare_die import template as bare_die
from packstudio.templates.package_library.bga import chip_array, pbga_wb
from packstudio.templates.package_library.core.default_library import template_defaults
from packstudio.templates.package_library.core.definitions import TemplateDefinition
from packstudio.templates.package_library.core.generator import generate_template
from packstudio.templates.package_library.core.parameters import TemplateRequest
from packstudio.templates.package_library.core.via_configuration import ViaConfiguration
from packstudio.templates.package_library.flip_chip import cbga_fc, pbga_fc
from packstudio.templates.package_library.leadframe import pqfp, qfn, sop

_definitions_lock = Lock()


@lru_cache(maxsize=1)
def definitions() -> dict[str, TemplateDefinition]:
    items = (
        chip_array.definition(),
        bare_die.definition(),
        cbga_fc.definition(),
        pbga_fc.definition(),
        pqfp.definition(),
        qfn.definition(),
        sop.definition(),
        pbga_wb.definition(),
    )
    return {item.id: item for item in items}


def catalog() -> list[dict[str, Any]]:
    # A cold cache can run its initializer once per concurrent caller.
    with _definitions_lock:
        items = definitions()
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
        for item in items.values()
    ]


def definition(template_id: str) -> TemplateDefinition:
    try:
        with _definitions_lock:
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
        bga={"representation": template_defaults(template_id)["default_bga_representation"]}
        if item.has_bga
        else None,
        vias=ViaConfiguration()
        if template_id != "chip_array" and any(f.key == "vias.enabled" for f in item.fields)
        else None,
    )


def generate(request: TemplateRequest) -> PackageModel:
    return generate_template(definition(request.template_id), request)
