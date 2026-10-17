import json
from collections import defaultdict
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from lxml import etree

from packstudio.api.app import app
from packstudio.domain.materials import ConductivityTensor
from packstudio.domain.thermal import HeatSource
from packstudio.exporters.floxml import export_floxml
from packstudio.templates.package_library.catalog import catalog, default_request, generate
from packstudio.templates.package_library.core.array_parameters import ArrayRepresentation

SCHEMA = etree.XMLSchema(
    etree.parse(str(Path(__file__).resolve().parents[3] / "output_format/floxml/xmlSchema.xsd"))
)
TEMPLATES = [item["id"] for item in catalog()]
client = TestClient(app)


@pytest.mark.parametrize("template_id", TEMPLATES)
def test_preserves_model_geometry_hierarchy_material_binding_and_power(template_id):
    model = generate(default_request(template_id))
    root = etree.fromstring(export_floxml(model))
    SCHEMA.assertValid(root)
    assert root.tag == "xml_case"
    assert root.findtext("name") == model.name
    assert root.find("solution_domain") is None
    assert root.find("all_grid_constraint") is None
    exported = {element.findtext("name"): element for element in root.findall(".//cuboid")}
    assert set(exported) == {block.id for block in model.blocks}
    powers = defaultdict(float)
    for source in model.heat_sources:
        powers[source.block_id] += source.power_w
    for block in model.blocks:
        element = exported[block.id]
        for axis in "xyz":
            assert float(element.findtext(f"position/{axis}")) == pytest.approx(
                getattr(block.origin, axis) / 1000, abs=1e-15
            )
            assert float(element.findtext(f"size/{axis}")) == pytest.approx(
                getattr(block.size, axis) / 1000, abs=1e-15
            )
        assert element.findtext("material") == block.material_id
        assert element.getparent().getparent().findtext("name") == block.parent_group_id
        assert json.loads(element.findtext("notes"))["structure_type"] == block.structure_type.value
        if block.id in powers:
            source = element.getparent().xpath("source[name=$name]", name=f"heat-{block.id}")[0]
            assert source.find("collapse") is None
            assert source.find("material") is None
            assert etree.tostring(source.find("size")) == etree.tostring(element.find("size"))
            attribute = root.xpath(
                "attributes/sources/source_att[name=$name]", name=source.findtext("source")
            )[0]
            assert attribute.findtext("type") == "total"
            assert float(attribute.findtext("power")) == pytest.approx(powers[block.id])
    assert len(root.findall(".//geometry/source")) == len(powers)
    for material, element in zip(model.materials, root.find("attributes/materials"), strict=True):
        assert element.findtext("name") == material.id
        assert float(element.findtext("density")) == material.density
        assert float(element.findtext("specific_heat")) == material.specific_heat
        for axis in "xyz":
            assert float(
                element.findtext("conductivity") or element.findtext(f"{axis}_conductivity")
            ) == getattr(material.conductivity, axis)
    for group in model.groups:
        assembly = root.xpath(".//assembly[name=$name]", name=group.id)[0]
        assert all(float(assembly.findtext(f"position/{axis}")) == 0 for axis in "xyz")
        if group.parent_id:
            assert assembly.getparent().getparent().findtext("name") == group.parent_id
    assert json.loads(root.findtext("notes"))["metadata"] == model.metadata


def test_custom_tensor_escaping_multiple_sources_and_finite_values():
    model = generate(default_request("bare_die"))
    material = model.materials[0].model_copy(
        update={
            "name": "自定义 <芯片> & --",
            "conductivity": ConductivityTensor(x=11, y=12, z=13),
        }
    )
    model = model.model_copy(
        update={
            "name": "方案 <A> & --",
            "materials": [material, *model.materials[1:]],
            "heat_sources": [
                HeatSource(id=f"s-{i}", name="source", block_id=model.blocks[0].id, power_w=power)
                for i, power in enumerate([1.25, 2.75])
            ],
        }
    )
    root = etree.fromstring(export_floxml(model))
    SCHEMA.assertValid(root)
    assert root.findtext("name") == model.name
    assert root.findtext("attributes/materials/orthotropic_material_att/y_conductivity") == "12"
    assert root.findtext("attributes/sources/source_att/power") == "4"
    assert len(root.findall(".//geometry/source")) == 1
    with pytest.raises(ValueError, match="finite number"):
        export_floxml(
            model.model_copy(
                update={
                    "materials": [material.model_copy(update={"density": float("inf")})],
                }
            )
        )


def test_discrete_bga_schema_and_solid_count():
    request = default_request("cbga_fc")
    request = request.model_copy(
        update={
            "bga": request.bga.model_copy(update={"representation": ArrayRepresentation.DISCRETE}),
        }
    )
    model = generate(request)
    root = etree.fromstring(export_floxml(model))
    SCHEMA.assertValid(root)
    assert len(root.findall(".//cuboid")) == len(model.blocks)


@pytest.mark.parametrize("template_id", TEMPLATES)
def test_download_api(template_id):
    response = client.post(
        f"/api/templates/{template_id}/export/floxml",
        json=default_request(template_id).model_dump(mode="json"),
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert response.headers["content-disposition"].endswith('.floxml"')
    SCHEMA.assertValid(etree.fromstring(response.content))


def test_invalid_download_request():
    request = default_request("bare_die").model_dump(mode="json")
    assert client.post("/api/templates/qfn/export/floxml", json=request).status_code == 422
    request["template_id"] = "missing"
    assert client.post("/api/templates/missing/export/floxml", json=request).status_code == 422
