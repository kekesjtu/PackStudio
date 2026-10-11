import pytest

from packstudio.material_catalog import MaterialCatalog
from packstudio.templates.package_library.catalog import default_request, definitions, generate
from packstudio.templates.package_library.core.materials import production_materials
from packstudio.templates.package_library.core.parameters import TemplateRequest


def test_native_defaults_drive_substrate_thickness_and_materials():
    model = generate(default_request("pbga_fc"))
    substrate = next(block for block in model.blocks if block.parent_group_id == "group-substrate")
    assert substrate.size.z == 1.15
    physical = next(
        material for material in model.materials if material.id == substrate.material_id
    )
    assert physical.name == "Substrate PBGAFC (Typical)"
    assert physical.conductivity.x == 20
    assert physical.conductivity.z == 4


def test_each_native_preset_material_assignment_matches_the_named_library():
    registry = production_materials()
    native = MaterialCatalog()
    for template_id, item in definitions().items():
        if template_id == "bare_die":
            continue
        footprint = next(f for f in item.fields if f.control == "footprint")
        for preset in footprint.presets:
            for group, identifier in preset.material_assignments.items():
                physical = registry[identifier]
                reference = native.read(physical.name)
                assert physical.density == reference["density"]["value"]
                assert physical.specific_heat == reference["specific_heat"]["value"]
                selection = next(s for s in item.material_selections if s.group_id == group)
                assert identifier in selection.options


@pytest.mark.parametrize(
    "template_id,subtype,preset",
    [
        ("pqfp", "mqfp", "LQFP_32_7X7mm"),
        ("sop", "tsop", "SOP_8_3_81x4_93"),
    ],
)
def test_subtype_and_footprint_mismatch_is_rejected(template_id, subtype, preset):
    with pytest.raises(ValueError, match="Package Type"):
        generate(
            TemplateRequest(
                template_id=template_id,
                overrides={
                    f"{template_id}.package.type": subtype,
                    f"{template_id}.footprint.size": preset,
                },
            )
        )
