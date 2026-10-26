import pytest
from fastapi.testclient import TestClient
from lxml import etree

from packstudio.api.app import app

client = TestClient(app)


def test_only_floxml_export_is_registered() -> None:
    export_paths = {path for path in app.openapi()["paths"] if "/export/" in path}
    assert export_paths == {"/api/templates/{template_id}/export/floxml"}


def test_template_catalog_lists_all_native_templates() -> None:
    response = client.get("/api/templates")

    assert response.status_code == 200
    assert [template["id"] for template in response.json()] == [
        "chip_array",
        "bare_die",
        "cbga_fc",
        "pbga_fc",
        "pqfp",
        "qfn",
        "sop",
        "pbga_wb",
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
    schema = client.get("/api/templates/cbga_fc/schema")
    defaults = client.get("/api/templates/cbga_fc/defaults")
    generated = client.post(
        "/api/templates/cbga_fc/generate",
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
        "chip_array",
        "bare_die",
        "cbga_fc",
        "pbga_fc",
        "pqfp",
        "qfn",
        "sop",
        "pbga_wb",
    ],
)
def test_every_native_export_is_downloadable_and_solver_payload_free(
    template_id: str,
) -> None:
    defaults = client.get(f"/api/templates/{template_id}/defaults").json()

    response = client.post(
        f"/api/templates/{template_id}/export/floxml",
        json=defaults,
    )
    root = etree.fromstring(response.content)
    names = {etree.QName(element).localname for element in root.iter()}

    assert response.status_code == 200
    assert etree.QName(root).localname == "xml_case"
    assert "Results" not in names
    assert "Mesh" not in names


def test_removed_alias_routes_and_old_template_ids_are_not_supported() -> None:
    assert client.get("/api/templates/bare_die/defaults").status_code == 200
    for path in ["reference/bare_die", "flip_chip_cbga", "fbga_fsbga", "qfp_family", "soic_family"]:
        assert client.get(f"/api/templates/{path}/defaults").status_code == 404


def test_default_pattern_survives_api_json_round_trip() -> None:
    from packstudio.templates.package_library.catalog import default_request, generate

    for template_id in ["cbga_fc", "pbga_fc", "chip_array", "pbga_wb"]:
        expected = generate(default_request(template_id))
        defaults = client.get(f"/api/templates/{template_id}/defaults").json()
        response = client.post(f"/api/templates/{template_id}/generate", json=defaults)
        assert response.status_code == 200
        assert response.json()["template_id"] == template_id
        assert (
            response.json()["metadata"]["solder_ball_count"]
            == expected.metadata["solder_ball_count"]
        )
