from fastapi.testclient import TestClient
from lxml import etree

from packstudio.api.app import app

client = TestClient(app)


def test_template_catalog_lists_only_flip_chip_cbga() -> None:
    response = client.get("/api/templates")

    assert response.status_code == 200
    assert [template["id"] for template in response.json()] == ["flip-chip-cbga"]
    assert response.json()[0]["solder_style_options"] == ["center_solder", "solder_removal"]
    assert "supported_patterns" not in response.json()[0]


def test_defaults_generate_reference_model() -> None:
    defaults = client.get("/api/templates/flip-chip-cbga/defaults")
    generated = client.post(
        "/api/templates/flip-chip-cbga/generate",
        json=defaults.json(),
    )

    assert defaults.status_code == 200
    assert defaults.json()["encapsulant"]["enabled"] is False
    assert "pattern" not in defaults.json()["solder_balls"]
    assert defaults.json()["solder_balls"]["center_solder_enabled"] is False
    assert defaults.json()["solder_balls"]["solder_removal_enabled"] is False
    assert defaults.json()["solder_balls"]["matrix_material"]["id"] == "air"
    assert defaults.json()["mesh"]["resolution"] == "standard"
    assert generated.status_code == 200
    assert generated.json()["metadata"]["solder_ball_equivalent_regions"] == 1
    assert "bga_static_air_block_count" not in generated.json()["metadata"]
    assert len(generated.json()["blocks"]) == 4


def test_pta_export_is_downloadable_and_has_no_solver_payload() -> None:
    defaults = client.get("/api/templates/flip-chip-cbga/defaults").json()

    response = client.post("/api/templates/flip-chip-cbga/export/pta", json=defaults)
    root = etree.fromstring(response.content)
    names = {etree.QName(element).localname for element in root.iter()}

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "attachment" in response.headers["content-disposition"]
    assert etree.QName(root).localname == "Structure"
    assert "Results" not in names
    assert "Mesh" not in names
    assert "MeshSizeXExpression" in names


def test_invalid_array_parameters_return_422() -> None:
    defaults = client.get("/api/templates/flip-chip-cbga/defaults").json()
    defaults["solder_balls"]["diameter"] = 2

    response = client.post("/api/templates/flip-chip-cbga/generate", json=defaults)

    assert response.status_code == 422


def test_discrete_flip_chip_bumps_return_422() -> None:
    defaults = client.get("/api/templates/flip-chip-cbga/defaults").json()
    defaults["flip_chip_bumps"]["representation"] = "discrete"

    response = client.post("/api/templates/flip-chip-cbga/generate", json=defaults)

    assert response.status_code == 422
    assert "only support anisotropic equivalent" in response.text


def test_removed_array_pattern_is_rejected() -> None:
    defaults = client.get("/api/templates/flip-chip-cbga/defaults").json()
    defaults["solder_balls"]["pattern"] = "staggered"

    response = client.post("/api/templates/flip-chip-cbga/generate", json=defaults)

    assert response.status_code == 422
    assert "pattern" in response.text
