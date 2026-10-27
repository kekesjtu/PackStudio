"""Default choices are concrete materials, including optional native branches."""

import pytest
from lxml import etree

from packstudio.exporters.floxml import export_floxml
from packstudio.material_catalog import MaterialCatalog
from packstudio.preset_catalog import PresetCatalog
from packstudio.templates.package_library.catalog import default_request, definitions, generate
from packstudio.templates.package_library.core.materials import material, production_materials


def test_material_categories_match_the_native_library_and_all_component_defaults_are_concrete():
    catalog = MaterialCatalog()
    for entry in production_materials().values():
        if entry.name in catalog.list_names():
            assert entry.category == catalog.read(entry.name)["category"]
    for definition in definitions().values():
        for selection in definition.material_selections:
            assert selection.default
            assert selection.default in selection.options
            assert material(selection.default).category
        for field in definition.fields:
            for preset in field.presets:
                assert all(preset.material_assignments.values())


@pytest.mark.parametrize("family", ["cbga_fc", "pbga_fc"])
def test_slug_and_adhesive_defaults_reach_generated_blocks_and_export(family):
    inputs = {
        "cover.type": "encapsulant",
        "slug.enabled": True,
        "slug.length": 4,
        "slug.width": 4,
        "slug.thickness": 0.4,
        "slug.diameter": 2,
        "slug.foot_length": 4.5,
        "slug.foot_width": 4.5,
        "slug.offset": 0.1,
        "slug.clearance": 0.1,
        "slug.adhesive_enabled": True,
    }
    model = generate(
        default_request(family).model_copy(
            update={"overrides": {f"{family}.{key}": value for key, value in inputs.items()}}
        )
    )
    expected = {"group-slug": "copper", "group-slug-adhesive": "stiffener-adhesive"}
    for group, identifier in expected.items():
        blocks = [b for b in model.blocks if b.parent_group_id == group]
        assert blocks and all(b.material_id == identifier for b in blocks)
    exported = etree.fromstring(export_floxml(model))
    for identifier in expected.values():
        assert exported.xpath(".//cuboid[material=$id]", id=identifier)


@pytest.mark.parametrize("region", ["upper", "lower"])
def test_built_up_regions_default_to_bt_and_keep_native_source_records_empty(region):
    request = default_request("pbga_fc").model_copy(
        update={
            "overrides": {f"pbga_fc.{region}.enabled": True, f"pbga_fc.{region}.thickness": 0.1}
        }
    )
    model = generate(request)
    block = next(b for b in model.blocks if b.id.startswith(region + "-region-"))
    assert block.material_id == "bt"
    assert next(m for m in model.materials if m.id == "bt").category == "Substrate Dielectrics"
    native = PresetCatalog().read_branch("PBGAFC_49_6X6mm")["groups"][region + "BuiltUpRegion"][
        "properties"
    ]["dielectricMaterial"]
    assert "value" not in native


def test_modeling_fields_share_a_schema_step_and_cbga_slug_is_conditionally_disabled():
    for family in ["bare_die", "cbga_fc", "pbga_fc", "chip_array"]:
        definition = definitions()[family]
        fields = {f.key: f for f in definition.fields}
        assert fields["grid.enabled"].step == fields["grid.density"].step == "modeling"
        for key in ["vias.modeling", "bond_wire.include"]:
            if key in fields:
                assert fields[key].step == "modeling"
    slug = next(f for f in definitions()["cbga_fc"].fields if f.key == "slug.enabled")
    assert slug.visible_when == {}
    assert slug.enabled_when == {"cover.type": "encapsulant"}
    assert "塑封体" in slug.help_text
    with pytest.raises(ValueError, match="inactive"):
        generate(
            default_request("cbga_fc").model_copy(
                update={"overrides": {"cbga_fc.slug.enabled": True}}
            )
        )
