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
    assert "solder_style_options" not in response.json()[0]
    assert "legacy_route" not in response.json()[0]
    assert "supported_patterns" not in response.json()[0]
    assert all(
        template["implementation_status"] == "packstudio_native"
        and template["runtime_reference_data_required"] is False
        for template in response.json()
    )


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
