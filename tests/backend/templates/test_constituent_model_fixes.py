"""Physical constituent edits must reach geometry-bound final equivalents."""

from math import pi

import pytest

from packstudio.domain.enums import StructureType
from packstudio.domain.materials import ConductivityTensor
from packstudio.templates.package_library.catalog import generate
from packstudio.templates.package_library.core.materials import material
from packstudio.templates.package_library.core.parameters import BgaConfiguration
from tests.backend.templates.reference_requests import reference_request


def changed(identifier, conductivity, density, specific_heat):
    return material(identifier).model_copy(
        update={
            "conductivity": ConductivityTensor.isotropic(conductivity),
            "density": density,
            "specific_heat": specific_heat,
        }
    )


@pytest.mark.parametrize("template", ["pbga_fc", "cbga_fc", "bare_die"])
def test_bump_normal_conductivity_density_and_heat_capacity_follow_both_constituents(template):
    overrides = (
        {"bumps.enabled": True, "bumps.total": 49, "die.length": 1.8, "die.width": 1.8}
        if template == "bare_die"
        else {}
    )
    solder = changed("solder-pb90", 72.0, 8000.0, 400.0)
    matrix = changed("underfill", 1.2, 1000.0, 1200.0)
    request = reference_request(template, overrides).model_copy(
        update={"custom_materials": [solder, matrix]}
    )
    model = generate(request)
    output = next(m for m in model.materials if m.id == "flip-chip-bumps-equivalent")
    fraction = 49 * pi * (0.12 / 2) ** 2 / (1.8 * 1.8)
    rho = fraction * 8000 + (1 - fraction) * 1000
    assert output.conductivity.z == pytest.approx(fraction * 72 + (1 - fraction) * 1.2)
    assert output.density == pytest.approx(rho)
    assert rho * output.specific_heat == pytest.approx(
        fraction * 8000 * 400 + (1 - fraction) * 1000 * 1200
    )
    baseline = generate(reference_request(template, overrides))
    before = next(m for m in baseline.materials if m.id == output.id)
    assert output.conductivity.x != before.conductivity.x
    assert output.conductivity.y != before.conductivity.y
    # Overrides of the derived material itself retain final precedence.
    explicit = output.model_copy(update={"density": 5000.0})
    model = generate(request.model_copy(update={"custom_materials": [solder, matrix, explicit]}))
    assert next(m for m in model.materials if m.id == output.id).density == 5000


@pytest.mark.parametrize("template", ["chip_array", "pbga_wb", "pbga_fc", "cbga_fc"])
@pytest.mark.parametrize("representation", ["equivalent", "discrete"])
def test_bga_constituent_edits_update_normal_mixture_or_discrete_solids(template, representation):
    solder = changed("solder-sn63", 80.0, 7000.0, 250.0)
    request = reference_request(template).model_copy(
        update={
            "bga": BgaConfiguration(representation=representation),
            "custom_materials": [solder],
        }
    )
    model = generate(request)
    materials = {m.id: m for m in model.materials}
    solids = [b for b in model.blocks if b.structure_type is StructureType.SOLDER_BALL]
    if representation == "discrete":
        assert all(materials[b.material_id] == solder for b in solids)
    else:
        air = material("static-air")
        area = sum(b.size.x * b.size.y for b in solids)
        # Count and diameter describe the physical solder, not its cuboid envelope.
        values = request.overrides
        count = model.metadata["solder_ball_count"]
        diameter = values[f"{template}.bga.diameter"]
        fraction = count * pi * (diameter / 2) ** 2 / area
        equivalent = materials["solder-ball-equivalent"]
        rho = fraction * 7000 + (1 - fraction) * air.density
        assert equivalent.conductivity.z == pytest.approx(
            fraction * 80 + (1 - fraction) * air.conductivity.z
        )
        assert equivalent.density == pytest.approx(rho)
        assert rho * equivalent.specific_heat == pytest.approx(
            fraction * 7000 * 250 + (1 - fraction) * air.density * air.specific_heat
        )


def test_wb_copper_edit_updates_both_traces_flag_and_via_even_when_vias_disabled():
    copper = changed("copper", 100.0, 8000.0, 400.0)
    substrate = changed("bt", 0.3, 1500.0, 900.0)
    for enabled in [True, False]:
        request = reference_request("pbga_wb", {"vias.enabled": enabled}).model_copy(
            update={"custom_materials": [copper, substrate]}
        )
        model = generate(request)
        materials = {m.id: m for m in model.materials}
        for identifier, fraction in [
            ("wirebond-trace-top", 0.3),
            ("wirebond-trace-bottom", 0.1),
            ("wirebond-die-flag", 0.6),
        ]:
            result = materials[identifier]
            rho = fraction * 8000 + (1 - fraction) * 1500
            assert result.conductivity.x == pytest.approx(fraction * 100 + (1 - fraction) * 0.3)
            assert result.density == pytest.approx(rho)
            assert result.specific_heat * rho == pytest.approx(
                fraction * 8000 * 400 + (1 - fraction) * 1500 * 900
            )
        if enabled:
            assert materials["wirebond-via"].conductivity.x == pytest.approx(0.36 * 100)
        else:
            assert "wirebond-via" not in materials


def test_bga_derived_override_and_removed_ball_pattern_remain_independent():
    request = reference_request("pbga_fc").model_copy(
        update={
            "bga": BgaConfiguration(
                representation="equivalent",
                solder_removal_enabled=True,
                removal_rows=1,
                removal_columns=1,
            ),
            "custom_materials": [changed("solder-sn63", 80.0, 7000.0, 250.0)],
        }
    )
    model = generate(request)
    equivalent = next(m for m in model.materials if m.id == "solder-ball-equivalent")
    assert model.metadata["solder_ball_count"] == 48
    explicit = equivalent.model_copy(update={"specific_heat": 600.0})
    model = generate(
        request.model_copy(update={"custom_materials": [*request.custom_materials, explicit]})
    )
    assert next(m for m in model.materials if m.id == equivalent.id).specific_heat == 600
