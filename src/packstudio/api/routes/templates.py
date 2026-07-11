from fastapi import APIRouter, HTTPException, Response

from packstudio.domain.model import PackageModel
from packstudio.exporters.pta_xml import export_pta_xml
from packstudio.templates.flip_chip_cbga.generator import generate_flip_chip_cbga
from packstudio.templates.flip_chip_cbga.parameters import (
    ArrayPattern,
    ArrayRepresentation,
    FlipChipCbgaParameters,
)

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("")
def list_templates() -> list[dict[str, object]]:
    return [
        {
            "id": "flip-chip-cbga",
            "name": "Flip Chip CBGA / BGA",
            "supported_patterns": [pattern.value for pattern in ArrayPattern],
            "supported_representations": [item.value for item in ArrayRepresentation],
        }
    ]


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
