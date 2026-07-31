import pytest

from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.catalog import (
    catalog,
    default_request,
    definitions,
    generate,
    schema,
)
from packstudio.templates.package_library.core.parameters import TemplateRequest


@pytest.mark.parametrize("template_id", list(definitions()))
def test_every_template_has_multiple_handwritten_size_presets(template_id: str) -> None:
    result = schema(template_id)
    fields = [field for step in result["steps"] for field in step["fields"]]
    footprint = next(field for field in fields if field["control"] == "footprint")

    assert footprint["classification"] == "jedec_preset"
    assert len(footprint["options"]) > 1
    assert set(footprint["options"]) == set(footprint["preset_values"])
    assert set(footprint["options"]) == set(footprint["option_labels"])


@pytest.mark.parametrize("template_id", list(definitions()))
def test_every_size_preset_generates_without_reference_data(template_id: str) -> None:
    item = definitions()[template_id]
    footprint = next(field for field in item.fields if field.control == "footprint")
    for option in footprint.options:
        defaults = default_request(template_id)
        request = defaults.model_copy(
            update={"overrides": {footprint.target_id(template_id): option}}
        )

        model = generate(request)

        assert model.metadata["footprint_size"] == option
        assert model.metadata["runtime_reference_data_required"] is False


def test_footprint_values_are_defaults_but_manual_dimensions_can_be_fine_tuned() -> None:
    model = generate(
        TemplateRequest(
            template_id="flip_chip_cbga",
            overrides={
                "flip_chip_cbga.footprint.size": "CBGAFC_64_7X7mm",
                "flip_chip_cbga.substrate.length": 7.4,
            },
        )
    )
    substrate = next(
        block for block in model.blocks if block.structure_type is StructureType.SUBSTRATE
    )

    assert substrate.size.x == pytest.approx(7.4)
    assert substrate.size.y == pytest.approx(7)
    assert model.metadata["solder_ball_count"] == 64
    assert model.metadata["solder_ball_footprint_x_mm"] == pytest.approx(6.1)
    assert model.metadata["solder_ball_footprint_y_mm"] == pytest.approx(6.1)


def test_fixed_outline_and_actual_die_are_not_presented_as_restricted_choices() -> None:
    for template_id in definitions():
        result = schema(template_id)
        fields = [field for step in result["steps"] for field in step["fields"]]
        properties = {field["property_name"] for field in fields}
        option_text = {str(option).lower() for field in fields for option in field["options"]}

        assert result["special_rules"]["outline_type"] == "standard_outline"
        assert result["special_rules"]["die_type"] == "actual_type"
        assert "outline_type" not in properties
        assert "die.type" not in properties
        assert "collapsed_cuboid" not in option_text
        assert "collapsedcuboid" not in option_text


def test_only_bga_templates_advertise_array_representation_choices() -> None:
    for item in catalog():
        expected = ["equivalent", "discrete"] if item["has_bga"] else []
        assert item["bga_representations"] == expected


@pytest.mark.parametrize("template_id", ("qfp_family", "soic_family"))
def test_qfp_and_soic_use_thermal_land_and_solder_instead_of_exposed_pad_option(
    template_id: str,
) -> None:
    result = schema(template_id)
    properties = {field["property_name"] for step in result["steps"] for field in step["fields"]}
    model = generate(
        TemplateRequest(
            template_id=template_id,
            overrides={f"{template_id}.thermal_land.enabled": True},
        )
    )

    assert "exposed_pad.enabled" not in properties
    assert "thermal_land.enabled" in properties
    assert any(block.parent_group_id == "group-thermal-land" for block in model.blocks)
    assert any(block.parent_group_id == "group-thermal-solder" for block in model.blocks)


def test_bare_die_bumps_use_a_thick_orthotropic_equivalent_layer() -> None:
    model = generate(
        TemplateRequest(
            template_id="bare_die",
            overrides={"bare_die.bumps.enabled": True},
        )
    )

    assert model.metadata["bump_representation"] == "thick_orthotropic_equivalent"
    bump = next(
        block for block in model.blocks if block.structure_type is StructureType.FLIP_CHIP_BUMP
    )
    assert bump.size.z == pytest.approx(0.1)
