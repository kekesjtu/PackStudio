from pathlib import Path

import pytest
from lxml import etree

import packstudio
from packstudio.domain.enums import StructureType
from packstudio.domain.geometry import find_overlapping_pairs
from packstudio.exporters.pta_xml import export_pta_xml
from packstudio.templates.package_library.catalog import (
    catalog,
    default_request,
    definitions,
    generate,
    schema,
)
from packstudio.templates.package_library.parameters import (
    BgaConfiguration,
    TemplateRequest,
)


def test_catalog_contains_eight_native_templates_without_runtime_data_dependency() -> None:
    items = catalog()

    assert [item["id"] for item in items] == [
        "flip_chip_cbga",
        "flip_chip_pbga",
        "wirebond_pbga",
        "fbga_fsbga",
        "qfn",
        "qfp_family",
        "soic_family",
        "bare_die",
    ]
    assert all(item["implementation_status"] == "packstudio_native" for item in items)
    assert all(item["runtime_reference_data_required"] is False for item in items)


def test_native_schemas_expose_only_handwritten_fields_and_special_rules() -> None:
    for template_id, item in definitions().items():
        result = schema(template_id)
        fields = [field for step in result["steps"] for field in step["fields"]]

        assert result["schema_version"] == "packstudio.wizard/v2"
        assert fields
        assert all(field["evidence_status"] == "implemented" for field in fields)
        assert all(
            forbidden not in field["property_name"]
            for field in fields
            for forbidden in ("staggered", "pattern", "solderBallMap")
        )
        assert result["has_bga"] is item.has_bga


@pytest.mark.parametrize("template_id", list(definitions()))
def test_every_native_baseline_is_valid_and_non_overlapping(template_id: str) -> None:
    model = generate(default_request(template_id))

    assert model.blocks
    assert model.materials
    assert find_overlapping_pairs(model.blocks) == []
    assert model.metadata["implementation"] == "packstudio-native"
    assert model.metadata["template_version"] == "2.0"
    assert model.metadata["mesh_data_included"] is False
    expected_power = 2 if template_id == "bare_die" else 0
    assert sum(source.power_w for source in model.heat_sources) == pytest.approx(expected_power)
    assert all(boundary.targets for boundary in model.boundaries)


def test_generation_and_export_do_not_read_reference_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_read(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("production template attempted a filesystem read")

    monkeypatch.setattr(Path, "read_text", reject_read)
    monkeypatch.setattr(etree, "parse", reject_read)

    for template_id in definitions():
        model = generate(default_request(template_id))
        payload = export_pta_xml(model)
        assert etree.fromstring(payload).tag.endswith("Structure")


def test_production_sources_do_not_contain_reference_repository_access() -> None:
    package_root = Path(packstudio.__file__).parent
    forbidden = ("flotherm_pack_data", "templates.reference", "etree.parse(", ".read_text(")

    for path in package_root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert all(token not in source for token in forbidden), path


def test_flip_chip_cbga_matches_reviewed_native_baseline() -> None:
    model = generate(default_request("flip_chip_cbga"))
    blocks = {block.structure_type: block for block in model.blocks}
    substrate = blocks[StructureType.SUBSTRATE]
    bump = blocks[StructureType.FLIP_CHIP_BUMP]
    solder = blocks[StructureType.SOLDER_BALL]

    assert substrate.origin.z == pytest.approx(0)
    assert substrate.size.model_dump() == pytest.approx({"x": 6, "y": 6, "z": 1.15})
    assert solder.origin.z == pytest.approx(-0.4)
    assert solder.origin.x == pytest.approx(-2.65)
    assert solder.size.x == pytest.approx(5.3)
    assert bump.origin.z == pytest.approx(1.15)
    assert bump.size.model_dump() == pytest.approx({"x": 1.8, "y": 1.8, "z": 0.1})
    assert model.metadata["flip_chip_bump_representation"] == ("thick_orthotropic_equivalent")


def test_native_numeric_parameter_updates_geometry_and_enforces_range() -> None:
    model = generate(
        TemplateRequest(
            template_id="bare_die",
            overrides={"bare_die.die.length": 4.5},
        )
    )
    die = next(block for block in model.blocks if block.structure_type is StructureType.DIE)

    assert die.size.x == pytest.approx(4.5)
    assert die.origin.x == pytest.approx(-2.25)
    with pytest.raises(ValueError, match="at most"):
        generate(
            TemplateRequest(
                template_id="bare_die",
                overrides={"bare_die.die.length": 80},
            )
        )


def test_bga_center_removal_and_explicit_omission_follow_task5_priority() -> None:
    model = generate(
        TemplateRequest(
            template_id="flip_chip_cbga",
            bga=BgaConfiguration(
                solder_removal_enabled=True,
                removal_rows=5,
                removal_columns=5,
                center_solder_enabled=True,
                center_solder_rows=3,
                center_solder_columns=3,
                omitted_cells=[{"row": 3, "column": 3}],
            ),
        )
    )

    assert model.metadata["solder_ball_count"] == 32
    assert any(block.structure_type is StructureType.STATIC_AIR for block in model.blocks)
    assert find_overlapping_pairs(model.blocks) == []


def test_only_bga_accepts_bga_configuration_and_complex_patterns_are_unknown() -> None:
    with pytest.raises(ValueError, match="only valid for BGA"):
        generate(
            TemplateRequest(
                template_id="bare_die",
                bga=BgaConfiguration(),
            )
        )
    with pytest.raises(ValueError, match="unknown production template parameters"):
        generate(
            TemplateRequest(
                template_id="flip_chip_cbga",
                overrides={"flip_chip_cbga.bga.staggered": True},
            )
        )


def test_inactive_conditional_parameter_is_rejected_by_backend() -> None:
    with pytest.raises(ValueError, match="inactive"):
        generate(
            TemplateRequest(
                template_id="qfn",
                overrides={"qfn.thermal_land.thickness": 0.2},
            )
        )


def test_material_assignment_uses_native_material_library() -> None:
    model = generate(
        TemplateRequest(
            template_id="bare_die",
            material_assignments={"group-die": "copper"},
        )
    )

    assert model.blocks[0].material_id == "copper"
    assert {material.id for material in model.materials} == {"copper"}
