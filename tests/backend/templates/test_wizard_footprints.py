import pytest

from packstudio.default_parameters import read_defaults
from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.catalog import (
    catalog,
    default_request,
    definitions,
    generate,
    schema,
)
from packstudio.templates.package_library.core.parameters import TemplateRequest

VERIFIED_JEDEC_OPTIONS = {
    "flip_chip_cbga": {"CBGAFC_49_6X6mm", "CBGAFC_81_8X8mm", "CBGAFC_144_10X10mm"},
    "flip_chip_pbga": {"PBGAFC_49_6X6mm", "PBGAFC_81_8X8mm", "PBGAFC_144_10X10mm"},
    "wirebond_pbga": {"PBGA_121_15X15mm", "PBGA_352_35X35mm", "PBGA_896_40X40mm"},
    "fbga_fsbga": {
        "ChipArray_24_4X4mm_0_8",
        "ChipArray_100_10X10mm_0_8",
        "ChipArray_324_19X19mm_1",
    },
    "qfn": {"QFN_12X12_100", "QFN_6X6_36", "QFN_3X3_8"},
    "qfp_family": {"LQFP_32_7X7mm", "LQFP_100_14X20mm", "LQFP_208_28X28mm"},
    "soic_family": {"SOP_8_3_81x4_93", "SOP_28_7_6x17_9", "SOP_44_13_3x28_2"},
}


@pytest.mark.parametrize("template_id", list(definitions()))
def test_every_template_has_multiple_handwritten_size_presets(template_id: str) -> None:
    result = schema(template_id)
    fields = [field for step in result["steps"] for field in step["fields"]]
    footprint = next(field for field in fields if field["control"] == "footprint")

    assert footprint["classification"] == "jedec_preset"
    assert len(footprint["options"]) > 1
    assert set(footprint["options"]) == set(footprint["preset_values"])
    assert set(footprint["options"]) == set(footprint["option_labels"])


def test_all_source_options_include_existing_captured_floxml_variants() -> None:
    definition_map = definitions()
    for template_id, expected in VERIFIED_JEDEC_OPTIONS.items():
        footprint = next(
            field for field in definition_map[template_id].fields if field.control == "footprint"
        )

        assert set(footprint.options) >= expected
    adapters = read_defaults("source_adapters.json", "packstudio.source-adapters/v1")
    for family, adapter in adapters["families"].items():
        records = read_defaults(f"flotherm/{family}.json", "packstudio.flotherm-presets/v1")
        footprint = next(field for field in definition_map[adapter["template_id"]].fields
                         if field.control == "footprint")
        assert set(footprint.options) == {record["id"] for record in records["records"]}


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
                "flip_chip_cbga.footprint.size": "CBGAFC_81_8X8mm",
                "flip_chip_cbga.substrate.length": 8.4,
            },
        )
    )
    substrate = next(
        block for block in model.blocks if block.structure_type is StructureType.SUBSTRATE
    )

    assert substrate.size.x == pytest.approx(8.4)
    assert substrate.size.y == pytest.approx(8)
    assert model.metadata["solder_ball_count"] == 81
    assert model.metadata["solder_ball_footprint_x_mm"] == pytest.approx(6.9)
    assert model.metadata["solder_ball_footprint_y_mm"] == pytest.approx(6.9)


@pytest.mark.parametrize(
    ("template_id", "footprint_value", "expected_length", "expected_width"),
    (
        ("flip_chip_cbga", "CBGAFC_81_8X8mm", 2.4, 2.4),
        ("flip_chip_cbga", "CBGAFC_144_10X10mm", 3.0, 3.0),
        ("flip_chip_pbga", "PBGAFC_81_8X8mm", 2.4, 2.4),
        ("wirebond_pbga", "PBGA_352_35X35mm", 10.5, 10.5),
        ("fbga_fsbga", "ChipArray_100_10X10mm_0_8", 3.0, 3.0),
        ("qfn", "QFN_6X6_36", 2.7, 2.7),
        ("qfp_family", "LQFP_100_14X20mm", 6.0, 4.2),
        ("soic_family", "SOP_28_7_6x17_9", 5.379, 2.286),
    ),
)
def test_verified_jedec_presets_update_die_xy_but_not_die_thickness(
    template_id: str,
    footprint_value: str,
    expected_length: float,
    expected_width: float,
) -> None:
    default_model = generate(default_request(template_id))
    model = generate(
        TemplateRequest(
            template_id=template_id,
            overrides={f"{template_id}.footprint.size": footprint_value},
        )
    )
    default_die = next(
        block for block in default_model.blocks if block.structure_type is StructureType.DIE
    )
    die = next(block for block in model.blocks if block.structure_type is StructureType.DIE)

    assert die.size.x == pytest.approx(expected_length)
    assert die.size.y == pytest.approx(expected_width)
    assert die.size.z == pytest.approx(default_die.size.z)


def test_every_source_preset_uses_declared_die_dimensions_without_uniform_scaling() -> None:
    adapters = read_defaults("source_adapters.json", "packstudio.source-adapters/v1")
    for template_id, definition in definitions().items():
        if template_id == "bare_die":
            continue
        footprint = next(field for field in definition.fields if field.control == "footprint")
        family = next(key for key, item in adapters["families"].items()
                      if item["template_id"] == template_id)
        records = {record["id"]: record for record in read_defaults(
            f"flotherm/{family}.json", "packstudio.flotherm-presets/v1")["records"]}
        for preset in footprint.presets:
            source = records[preset.value]["values"]
            assert preset.values["die.length"] == source["Ld"]
            assert preset.values["die.width"] == source["Wd"]
            assert preset.values["die.thickness"] == source["td"]


def test_verified_presets_keep_component_specific_nonuniform_rules() -> None:
    definition_map = definitions()
    pbga = next(
        field for field in definition_map["wirebond_pbga"].fields if field.control == "footprint"
    )
    qfp = next(
        field for field in definition_map["qfp_family"].fields if field.control == "footprint"
    )
    pbga_35 = next(preset for preset in pbga.presets if preset.value == "PBGA_352_35X35mm")
    qfp_14x20 = next(preset for preset in qfp.presets if preset.value == "LQFP_100_14X20mm")

    assert pbga_35.values["encapsulant.length"] == pytest.approx(30)
    assert pbga_35.values["flag.length"] == pytest.approx(12.5)
    assert pbga_35.values["substrate.thickness"] == pytest.approx(0.56)
    assert qfp_14x20.values["body.length"] == pytest.approx(20)
    assert qfp_14x20.values["body.width"] == pytest.approx(14)
    assert qfp_14x20.values["leads.count_x"] == 30
    assert qfp_14x20.values["leads.count_y"] == 20


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
