import json
from collections import defaultdict
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from lxml import etree

from packstudio.api.app import app
from packstudio.domain.materials import ConductivityTensor
from packstudio.domain.thermal import HeatSource
from packstudio.exporters.ecxml import export_ecxml
from packstudio.templates.flip_chip_cbga.parameters import ArrayRepresentation
from packstudio.templates.package_library.catalog import catalog, default_request, generate

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "output_format/ecxml/ECXML.xsd"
SCHEMA = etree.XMLSchema(etree.parse(str(SCHEMA_PATH)))
TEMPLATES = [item["id"] for item in catalog()]
client = TestClient(app)


@pytest.mark.parametrize("template_id", TEMPLATES)
def test_ecxml_preserves_physical_blocks_materials_power_and_groups(template_id: str) -> None:
    model = generate(default_request(template_id))
    root = etree.fromstring(export_ecxml(model))
    SCHEMA.assertValid(root)
    assert root.tag == "neutralXML"
    assert root.findtext("name") == model.name
    assert root.findtext("producer") == "FloTHERM"
    assert root.find("solutionDomain") is None
    exported = {element.findtext("name"): element for element in root.findall(".//solid3dBlock")}
    assert set(exported) == {block.id for block in model.blocks}
    powers: dict[str, float] = defaultdict(float)
    for source in model.heat_sources:
        powers[source.block_id] += source.power_w
    for block in model.blocks:
        element = exported[block.id]
        for axis in ("x", "y", "z"):
            assert float(element.findtext(f"location/{axis}")) == pytest.approx(
                getattr(block.origin, axis) / 1000, abs=1e-15
            )
            assert float(element.findtext(f"size/{axis}")) == pytest.approx(
                getattr(block.size, axis) / 1000, abs=1e-15
            )
        assert element.findtext("material") == block.material_id
        assert element.getparent().getparent().findtext("name") == block.parent_group_id
        assert float(element.findtext("powerDissipation")) == pytest.approx(powers[block.id])
    assert sum(float(item.findtext("powerDissipation")) for item in exported.values()) == (
        pytest.approx(sum(item.power_w for item in model.heat_sources))
    )
    for material, element in zip(model.materials, root.findall("materials/material"), strict=True):
        assert element.findtext("name") == material.id
        assert float(element.findtext("density")) == material.density
        assert float(element.findtext("specific_heat")) == material.specific_heat
        thermal = element.find("thermalConductivity")
        if thermal.find("isotropic") is not None:
            assert float(thermal.findtext("isotropic/conductivity")) == material.conductivity.x
        else:
            for axis in ("x", "y", "z"):
                assert float(thermal.findtext(f"orthotropic/{axis}")) == getattr(
                    material.conductivity, axis
                )
    for group in model.groups:
        element = root.xpath(".//assembly[name=$name]", name=group.id)[0]
        if group.parent_id is not None:
            assert element.getparent().getparent().findtext("name") == group.parent_id
    audit = _audit(root)
    assert audit["boundaries"] == [item.model_dump(mode="json") for item in model.boundaries]
    assert audit["metadata"] == model.metadata


def test_multiple_sources_and_custom_material_are_preserved_without_duplicate_geometry() -> None:
    model = generate(default_request("bare_die"))
    block = model.blocks[0]
    material = model.materials[0].model_copy(
        update={"name": "自定义 <芯片> & --", "conductivity": ConductivityTensor(x=11, y=12, z=13)}
    )
    model = model.model_copy(
        update={
            "name": "方案 <A> & --",
            "materials": [material, *model.materials[1:]],
            "heat_sources": [
                HeatSource(id="one", name="one", block_id=block.id, power_w=1.25),
                HeatSource(id="two", name="two", block_id=block.id, power_w=2.75),
            ],
        }
    )
    root = etree.fromstring(export_ecxml(model))
    SCHEMA.assertValid(root)
    assert root.findtext("name") == model.name
    assert len(root.findall(".//solid3dBlock")) == len(model.blocks)
    assert root.findtext(".//solid3dBlock/powerDissipation") == "4"
    assert _audit(root)["material_names"][material.id] == material.name
    assert root.findtext("materials/material/thermalConductivity/orthotropic/y") == "12"


def test_discrete_bga_exports_every_ball_in_si_units() -> None:
    request = default_request("flip_chip_cbga")
    request = request.model_copy(
        update={
            "bga": request.bga.model_copy(update={"representation": ArrayRepresentation.DISCRETE})
        }
    )
    model = generate(request)
    root = etree.fromstring(export_ecxml(model))
    SCHEMA.assertValid(root)
    assert len(root.findall(".//solid3dBlock")) == len(model.blocks)


def test_nonfinite_material_value_is_rejected() -> None:
    model = generate(default_request("bare_die"))
    materials = [model.materials[0].model_copy(update={"density": float("inf")})]
    with pytest.raises(ValueError, match="finite number"):
        export_ecxml(model.model_copy(update={"materials": materials}))


@pytest.mark.parametrize("template_id", TEMPLATES)
def test_ecxml_download_api(template_id: str) -> None:
    response = client.post(
        f"/api/templates/{template_id}/export/ecxml",
        json=default_request(template_id).model_dump(mode="json"),
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert response.headers["content-disposition"].endswith('.ecxml"')
    assert "not-applied" in response.headers["x-packstudio-export-warnings"]
    SCHEMA.assertValid(etree.fromstring(response.content))


def test_ecxml_api_rejects_mismatched_and_unknown_templates() -> None:
    request = default_request("bare_die").model_dump(mode="json")
    assert client.post("/api/templates/qfn/export/ecxml", json=request).status_code == 422
    request["template_id"] = "missing"
    assert client.post("/api/templates/missing/export/ecxml", json=request).status_code == 422


def _audit(root: etree._Element) -> dict:
    return json.loads(root.xpath("comment()")[0].text.removeprefix("PackStudio export metadata: "))
