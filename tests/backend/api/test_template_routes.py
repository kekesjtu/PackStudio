from fastapi.testclient import TestClient
from lxml import etree

from packstudio.api.app import app

client = TestClient(app)


def test_template_catalog_lists_only_flip_chip_cbga() -> None:
    response = client.get("/api/templates")

    assert response.status_code == 200
    assert [template["id"] for template in response.json()] == ["flip-chip-cbga"]


def test_defaults_generate_reference_model() -> None:
    defaults = client.get("/api/templates/flip-chip-cbga/defaults")
    generated = client.post(
        "/api/templates/flip-chip-cbga/generate",
        json=defaults.json(),
    )

    assert defaults.status_code == 200
    assert generated.status_code == 200
    assert generated.json()["metadata"]["solder_ball_equivalent_regions"] == 5
    assert len(generated.json()["blocks"]) == 8


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
    assert not any(name.startswith("Mesh") for name in names)


def test_invalid_array_parameters_return_422() -> None:
    defaults = client.get("/api/templates/flip-chip-cbga/defaults").json()
    defaults["solder_balls"]["diameter"] = 2

    response = client.post("/api/templates/flip-chip-cbga/generate", json=defaults)

    assert response.status_code == 422
