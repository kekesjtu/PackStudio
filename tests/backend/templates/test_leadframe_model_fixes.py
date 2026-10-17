"""Final binding and signed-height regressions, with independent PACK evidence."""

from collections import Counter
from math import hypot, pi
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

from packstudio.templates.package_library.catalog import definition, generate
from packstudio.templates.package_library.core.materials import material
from tests.backend.templates.reference_requests import reference_request

ROOT = Path(__file__).parents[3]


def properties(item):
    return (*[getattr(item.conductivity, a) for a in "xyz"], item.density, item.specific_heat)


@pytest.mark.parametrize("template", ["pqfp", "sop"])
def test_final_lead_envelopes_retain_native_equivalent_properties(template):
    model = generate(reference_request(template))
    originals = {
        e.findtext("name"): e
        for e in ET.parse(ROOT / f"flotherm_pack_data/templates/{template}/baseline/model.xml")
        .getroot()
        .find("attributes/materials")
    }
    mapping = (
        {
            "pqfp-leadframe-inner-x": "LeadFrame_1x",
            "pqfp-leadframe-inner-y": "LeadFrame_1y",
            "pqfp-leadframe-outer-x": "LeadFrame_2x",
            "pqfp-leadframe-outer-y": "LeadFrame_2y",
            "pqfp-tie-bar": "tie_bar1",
        }
        if template == "pqfp"
        else {"sop-leadframe-inner": "LeadFrame_1", "sop-leadframe-outer": "LeadFrame_2"}
    )
    actual = {m.id: m for m in model.materials}
    for identifier, native_name in mapping.items():
        original = originals[native_name]
        scalar = original.findtext("conductivity")
        tensor = (
            [float(scalar)] * 3
            if scalar
            else [float(original.findtext(f"{a}_conductivity")) for a in "xyz"]
            if original.find("x_conductivity") is not None
            else [float(original.findtext("in_plane_conductivity"))] * 2
            + [float(original.findtext("normal_conductivity"))]
        )
        assert properties(actual[identifier]) == pytest.approx(
            (
                *tensor,
                float(original.findtext("density")),
                float(original.findtext("specific_heat")),
            )
        )
    assert all(
        b.material_id in mapping for b in model.blocks if b.parent_group_id == "group-lead-frame"
    )
    if template == "sop":
        assert all(
            b.material_id != "sop-die-flag"
            for b in model.blocks
            if b.parent_group_id == "group-tie-bars"
        )


@pytest.mark.parametrize("template", ["pqfp", "sop"])
def test_lead_width_pitch_and_constituent_edits_recompute_envelope(template):
    choice = next(
        s.default
        for s in definition(template).material_selections
        if s.group_id == "group-lead-frame"
    )
    metal = material(choice).model_copy(
        update={
            "density": 8000.0,
            "specific_heat": 400.0,
            "conductivity": material(choice).conductivity.model_copy(
                update=dict.fromkeys("xyz", 200.0)
            ),
        }
    )
    request = reference_request(template, {"leads.width": 0.3, "leads.pitch": 0.9}).model_copy(
        update={"custom_materials": [metal]}
    )
    model = generate(request)
    matrix = material("epoxy-mold")
    fraction = 0.3 / 0.9
    rho = fraction * metal.density + (1 - fraction) * matrix.density
    cp = (
        fraction * metal.density * metal.specific_heat
        + (1 - fraction) * matrix.density * matrix.specific_heat
    ) / rho
    identifier = f"{template}-leadframe-inner" + ("-x" if template == "pqfp" else "")
    output = next(m for m in model.materials if m.id == identifier)
    assert output.conductivity.x == pytest.approx(fraction * 200 + (1 - fraction) * 0.68)
    assert output.density == pytest.approx(rho)
    assert output.specific_heat == pytest.approx(cp)


def test_rectangular_tie_bar_uses_actual_geometry_and_keeps_explicit_override_priority():
    request = reference_request("pqfp", {"body.length": 8.0})
    model = generate(request)
    result = next(m for m in model.materials if m.id == "pqfp-tie-bar")
    a, b = (8 - 2.94) / 2, (7 - 2.94) / 2
    assert result.conductivity.x == pytest.approx(301.5 / (hypot(a, b) * (1 / a + 1 / b)))
    override = result.model_copy(update={"density": 7000.0})
    model = generate(request.model_copy(update={"custom_materials": [override]}))
    assert next(m for m in model.materials if m.id == override.id).density == 7000


def test_negative_height_raw_geometry_and_wire_material_match_native_pack():
    request = reference_request("pqfp", {"flag.downset": 0.44})
    item = definition("pqfp")
    values = item.validate_request(request)
    built = item.builder(values, item.resolve_material_request(request, values))
    with ZipFile(ROOT / "docs/validation/floxml/evidence.zip") as archive:
        native = ET.fromstring(archive.read("cases/qfp-negative/native.xml"))
    expected = Counter(
        tuple(
            round(float(e.findtext(f"{field}/{a}")) * 1000, 9)
            for field in ["position", "size"]
            for a in "xyz"
        )
        for e in native.findall(".//cuboid")
    )
    actual = Counter(tuple(round(v, 9) for v in (*d.origin, *d.size)) for d in built.drafts)
    assert actual == expected
    model = generate(request)
    output = next(m for m in model.materials if m.id == "pqfp-bondwire-x")
    original = next(
        e for e in native.find("attributes/materials") if e.findtext("name") == "bondwire1"
    )
    assert output.conductivity.x == pytest.approx(float(original.findtext("x_conductivity")))
    # Independent dimensional formula uses absolute length, not signed displacement.
    fraction = 8 * pi * 0.03**2 / 4 * 2 / ((0.84 + abs(0.35 + 0.038 - 0.44)) * 2.1 * 0.03)
    assert output.conductivity.x == pytest.approx(
        fraction * material("gold").conductivity.x + (1 - fraction) * 0.68
    )


@pytest.mark.parametrize("downset", [0.2, 0.384, 0.388, 0.389, 0.44, 0.6])
def test_height_sign_boundaries_generate_positive_nonoverlapping_blocks_and_conserve_power(downset):
    request = reference_request("pqfp", {"flag.downset": downset}).model_copy(
        update={"die_power_w": 2.5}
    )
    model = generate(request)
    assert sum(s.power_w for s in model.heat_sources) == pytest.approx(2.5)
    assert all(min(b.size.x, b.size.y, b.size.z) > 0 for b in model.blocks)
    if downset == 0.388:
        assert not any(
            b.metadata.get("boolean_source_id", "").startswith("bond-wire-v-") for b in model.blocks
        )
