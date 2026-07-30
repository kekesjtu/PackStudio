from fastapi import APIRouter, HTTPException, Response

from packstudio.domain.model import PackageModel
from packstudio.exporters.pta_xml import export_pta_xml
from packstudio.templates.flip_chip_cbga.generator import generate_flip_chip_cbga
from packstudio.templates.flip_chip_cbga.parameters import FlipChipCbgaParameters
from packstudio.templates.package_library.catalog import (
    catalog,
    default_request,
    generate,
    schema,
)
from packstudio.templates.package_library.core.materials import production_materials
from packstudio.templates.package_library.core.parameters import TemplateRequest

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("")
def list_templates() -> list[dict[str, object]]:
    templates = catalog()
    for item in templates:
        if item["id"] == "flip_chip_cbga":
            item["legacy_route"] = "flip-chip-cbga"
            item["solder_style_options"] = ["center_solder", "solder_removal"]
            item["flip_chip_layout"] = "full"
    return templates


@router.get("/flip-chip-cbga/defaults", response_model=FlipChipCbgaParameters)
def flip_chip_cbga_defaults() -> FlipChipCbgaParameters:
    return FlipChipCbgaParameters()


@router.post("/flip-chip-cbga/generate", response_model=PackageModel)
def generate_model(parameters: FlipChipCbgaParameters) -> PackageModel:
    try:
        return generate_flip_chip_cbga(parameters)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/flip-chip-cbga/export/pta")
def export_model_to_pta(parameters: FlipChipCbgaParameters) -> Response:
    try:
        model = generate_flip_chip_cbga(parameters)
        payload = export_pta_xml(model)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return Response(
        content=payload,
        media_type="application/xml",
        headers={"Content-Disposition": 'attachment; filename="flip-chip-cbga.xml"'},
    )


@router.get("/materials")
@router.get("/reference/materials", include_in_schema=False)
def template_materials() -> list[dict[str, object]]:
    return [material.model_dump(mode="json") for material in production_materials().values()]


@router.get("/{template_id}/schema")
@router.get("/reference/{template_id}/schema")
def template_schema(template_id: str) -> dict[str, object]:
    try:
        return schema(template_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{template_id}/defaults")
@router.get("/reference/{template_id}/defaults")
def template_defaults(template_id: str) -> TemplateRequest:
    try:
        return default_request(template_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{template_id}/generate", response_model=PackageModel)
@router.post("/reference/{template_id}/generate", response_model=PackageModel)
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


@router.post("/{template_id}/export/pta")
@router.post("/reference/{template_id}/export/pta")
def export_library_model_to_pta(
    template_id: str,
    request: TemplateRequest,
) -> Response:
    if request.template_id != template_id:
        raise HTTPException(status_code=422, detail="request template_id does not match route")
    try:
        payload = export_pta_xml(generate(request))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return Response(
        content=payload,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="{template_id.replace("_", "-")}.xml"'
        },
    )
