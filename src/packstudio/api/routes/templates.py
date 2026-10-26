from fastapi import APIRouter, HTTPException, Response

from packstudio.domain.model import PackageModel
from packstudio.exporters.floxml import export_floxml
from packstudio.templates.package_library.catalog import (
    catalog,
    default_request,
    definition,
    generate,
    schema,
)
from packstudio.templates.package_library.core.materials import (
    material_id_for_name,
    production_materials,
)
from packstudio.templates.package_library.core.parameters import TemplateRequest
from packstudio.templates.package_library.core.preset_request import resolve_preset_request

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("")
def list_templates() -> list[dict[str, object]]:
    return catalog()


@router.get("/materials")
def template_materials() -> list[dict[str, object]]:
    return [
        material.model_dump(mode="json")
        for material in production_materials().values()
        if material.id == material_id_for_name(material.name)
    ]


@router.get("/{template_id}/schema")
def template_schema(template_id: str) -> dict[str, object]:
    try:
        return schema(template_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{template_id}/defaults")
def template_defaults(template_id: str) -> TemplateRequest:
    try:
        return resolve_preset_request(definition(template_id), default_request(template_id))[0]
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{template_id}/generate", response_model=PackageModel)
def generate_library_model(
    template_id: str,
    request: TemplateRequest,
) -> PackageModel:
    if request.template_id != template_id:
        raise HTTPException(status_code=422, detail="request template_id does not match route")
    try:
        return generate(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/{template_id}/export/floxml")
def export_library_model_to_floxml(template_id: str, request: TemplateRequest) -> Response:
    if request.template_id != template_id:
        raise HTTPException(status_code=422, detail="request template_id does not match route")
    try:
        payload = export_floxml(generate(request))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return Response(
        content=payload,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="{template_id}.floxml"',
            "X-PackStudio-Export-Warnings": "face-boundaries-not-applied",
        },
    )
