import pytest
from fastapi.testclient import TestClient
from lxml import etree

from packstudio.api.app import app

client = TestClient(app)


def test_template_catalog_lists_all_native_templates() -> None:
    response = client.get("/api/templates")

    assert response.status_code == 200
    assert [template["id"] for template in response.json()] == [
        "flip_chip_cbga",
        "flip_chip_pbga",
        "wirebond_pbga",
        "fbga_fsbga",
        "qfn",
        "qfp_family",
        "soic_family",
        "bare_die",
    ]
    assert response.json()[0]["solder_style_options"] == ["center_solder", "solder_removal"]
    assert "supported_patterns" not in response.json()[0]
    assert all(
        template["implementation_status"] == "packstudio_native"
        and template["runtime_reference_data_required"] is False
        for template in response.json()
    )


def test_defaults_generate_legacy_flip_chip_model() -> None:
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


def test_native_schema_and_generation_use_packstudio_special_rules() -> None:
    schema = client.get("/api/templates/flip_chip_cbga/schema")
    defaults = client.get("/api/templates/flip_chip_cbga/defaults")
    generated = client.post(
        "/api/templates/flip_chip_cbga/generate",
        json=defaults.json(),
    )

    assert schema.status_code == 200
    properties = {
        field.get("property_name") for step in schema.json()["steps"] for field in step["fields"]
    }
    assert all("staggered" not in property_name for property_name in properties)
    assert schema.json()["schema_version"] == "packstudio.wizard/v2"
    assert defaults.json()["bga"]["representation"] == "equivalent"
    assert generated.status_code == 200
    assert generated.json()["metadata"]["implementation"] == "packstudio-native"
    assert generated.json()["metadata"]["solder_ball_footprint_x_mm"] == pytest.approx(5.3)
    assert generated.json()["metadata"]["flip_chip_bump_footprint_x_mm"] == pytest.approx(1.8)
    assert generated.json()["metadata"]["flip_chip_bump_representation"] == (
        "thick_orthotropic_equivalent"
    )


@pytest.mark.parametrize(
    "template_id",
    [
        "flip_chip_cbga",
        "flip_chip_pbga",
        "wirebond_pbga",
        "fbga_fsbga",
        "qfn",
        "qfp_family",
        "soic_family",
        "bare_die",
    ],
)
def test_every_native_export_is_downloadable_and_solver_payload_free(
    template_id: str,
) -> None:
    defaults = client.get(f"/api/templates/{template_id}/defaults").json()

    response = client.post(
        f"/api/templates/{template_id}/export/pta",
        json=defaults,
    )
    root = etree.fromstring(response.content)
    names = {etree.QName(element).localname for element in root.iter()}

    assert response.status_code == 200
    assert etree.QName(root).localname == "Structure"
    assert "Results" not in names
    assert "Mesh" not in names


def test_reference_route_is_only_a_compatibility_alias() -> None:
    native = client.get("/api/templates/bare_die/defaults")
    alias = client.get("/api/templates/reference/bare_die/defaults")

    assert native.status_code == 200
    assert alias.status_code == 200
    assert alias.json() == native.json()
