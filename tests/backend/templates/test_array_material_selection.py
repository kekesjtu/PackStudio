"""Selected constituents must reach layer mixtures, solids, and exports."""

from math import pi

import pytest
from lxml import etree

from packstudio.domain.enums import StructureType
from packstudio.domain.materials import ConductivityTensor
from packstudio.exporters.floxml import export_floxml
from packstudio.templates.package_library.catalog import default_request, generate, schema
from packstudio.templates.package_library.core.materials import material, material_id_for_name
from packstudio.templates.package_library.core.parameters import BgaConfiguration
from tests.backend.templates.reference_requests import reference_request


def customized(identifier, conductivity, density, specific_heat):
    return material(identifier).model_copy(
        update={
            "conductivity": ConductivityTensor(**dict(zip("xyz", conductivity, strict=True))),
            "density": density,
            "specific_heat": specific_heat,
        }
    )


@pytest.mark.parametrize("template", ["cbga_fc", "pbga_fc", "bare_die"])
def test_selected_bump_and_underfill_materials_drive_all_mixture_properties(template):
    matrix_id = material_id_for_name("Glass (Typical)")
    solder = customized("solder-sn63", (70, 80, 90), 7000, 300)
    matrix = customized(matrix_id, (1, 2, 3), 1000, 1200)
    overrides = {"bumps.enabled": True} if template == "bare_die" else {}
    request = reference_request(template, overrides).model_copy(
        update={
            "material_assignments": {
                "group-bump-solder": solder.id,
                "group-underfill": matrix.id,
            },
            "custom_materials": [solder, matrix],
        }
    )
    model = generate(request)
    result = next(m for m in model.materials if m.id == "flip-chip-bumps-equivalent")
    block = next(b for b in model.blocks if b.structure_type is StructureType.FLIP_CHIP_BUMP)
    fraction = (
        model.metadata["flip_chip_bump_count"]
        * pi
        * (0.12 / 2) ** 2
        / (block.size.x * block.size.y)
    )
    density = fraction * 7000 + (1 - fraction) * 1000
    assert result.conductivity.z == pytest.approx(fraction * 90 + (1 - fraction) * 3)
    assert result.density == pytest.approx(density)
    assert result.specific_heat * density == pytest.approx(
        fraction * 7000 * 300 + (1 - fraction) * 1000 * 1200
    )
    baseline = next(
        m for m in generate(reference_request(template, overrides)).materials if m.id == result.id
    )
    assert result.conductivity.x != baseline.conductivity.x
    assert result.conductivity.y != baseline.conductivity.y
    assert block.material_id == result.id
    explicit = result.model_copy(update={"density": 4500.0})
    overridden = generate(
        request.model_copy(update={"custom_materials": [solder, matrix, explicit]})
    )
    assert next(m for m in overridden.materials if m.id == result.id).density == 4500


@pytest.mark.parametrize("template", ["cbga_fc", "pbga_fc", "chip_array", "pbga_wb"])
@pytest.mark.parametrize("representation", ["equivalent", "discrete"])
def test_selected_bga_solder_reaches_both_center_and_perimeter_and_keeps_air(
    template, representation
):
    solder = customized("solder-pb90", (60, 70, 80), 7500, 350)
    request = reference_request(template).model_copy(
        update={
            "material_assignments": {"group-bga-solder": solder.id},
            "custom_materials": [solder],
            "bga": BgaConfiguration(
                representation=representation,
                center_solder_enabled=True,
                center_solder_rows=1,
                center_solder_columns=1,
                solder_removal_enabled=True,
                removal_rows=3,
                removal_columns=3,
            ),
        }
    )
    model = generate(request)
    solids = [b for b in model.blocks if b.structure_type is StructureType.SOLDER_BALL]
    assert {b.parent_group_id for b in solids} == {"group-solder-ball", "group-center-solder-ball"}
    count = (
        request.overrides[f"{template}.bga.rows"] * request.overrides[f"{template}.bga.columns"] - 8
    )
    assert model.metadata["solder_ball_count"] == count
    assert all(
        b.material_id == "static-air"
        for b in model.blocks
        if b.structure_type is StructureType.STATIC_AIR
    )
    materials = {m.id: m for m in model.materials}
    if representation == "discrete":
        assert all(materials[b.material_id] == solder for b in solids)
    elif template != "pbga_wb":
        air = material("static-air")
        for group, physical_count in [
            ("group-solder-ball", count - 1),
            ("group-center-solder-ball", 1),
        ]:
            regions = [b for b in solids if b.parent_group_id == group]
            output = materials[regions[0].material_id]
            fraction = (
                physical_count
                * pi
                * (request.overrides[f"{template}.bga.diameter"] / 2) ** 2
                / sum(b.size.x * b.size.y for b in regions)
            )
            assert output.conductivity.z == pytest.approx(
                fraction * 80 + (1 - fraction) * air.conductivity.z
            )
            assert output.density == pytest.approx(fraction * 7500 + (1 - fraction) * air.density)
            assert output.conductivity.x == output.conductivity.y == air.conductivity.x
            assert output.specific_heat * output.density == pytest.approx(
                fraction * 7500 * 350 + (1 - fraction) * air.density * air.specific_heat
            )
    else:
        result = materials["solder-ball-equivalent"]
        assert all(b.material_id == result.id for b in solids)
        fraction = (
            count
            * pi
            * (request.overrides[f"{template}.bga.diameter"] / 2) ** 2
            / sum(b.size.x * b.size.y for b in solids)
        )
        air = material("static-air")
        density = fraction * 7500 + (1 - fraction) * air.density
        assert result.conductivity.x == air.conductivity.x
        assert result.conductivity.y == air.conductivity.y
        assert result.conductivity.z == pytest.approx(
            fraction * 80 + (1 - fraction) * air.conductivity.z
        )
        assert result.density == pytest.approx(density)
        assert result.specific_heat * density == pytest.approx(
            fraction * 7500 * 350 + (1 - fraction) * air.density * air.specific_heat
        )
    root = etree.fromstring(export_floxml(model))
    for identifier in {b.material_id for b in solids}:
        exported = root.xpath(f"./attributes/materials/*[name='{identifier}']")[0]
        assert float(exported.findtext("density")) == pytest.approx(materials[identifier].density)


def test_selection_contract_and_inactive_bare_die_materials_are_validated():
    for template in ("cbga_fc", "pbga_fc"):
        fields = [f for s in schema(template)["steps"] for f in s["fields"]]
        for group in ("group-bump-solder", "group-underfill", "group-bga-solder"):
            field = next(f for f in fields if f["material_group_id"] == group)
            assert len(field["options"]) > 1
            assert field["default"] in field["options"]
    with pytest.raises(ValueError, match="not allowed"):
        generate(
            default_request("cbga_fc").model_copy(
                update={"material_assignments": {"group-bump-solder": "missing-material"}}
            )
        )
    with pytest.raises(ValueError, match="inactive"):
        generate(
            default_request("bare_die").model_copy(
                update={"material_assignments": {"group-underfill": "underfill"}}
            )
        )
