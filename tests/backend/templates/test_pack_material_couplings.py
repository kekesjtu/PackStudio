"""Golden FloXML material checks for all eleven retained parameter couplings."""

import json
from pathlib import Path
from xml.etree import ElementTree

import pytest

from packstudio.templates.package_library.catalog import default_request, generate
from packstudio.templates.package_library.core.materials import material
from tests.backend.templates.reference_requests import reference_request

ROOT = Path(__file__).parents[3] / "flotherm_pack_data/templates"
FIELDS = {
    "pbga_wb": {"numberOfBondWiresNw": "bond_wire.total", "platingThicknessTpl": "vias.plating"},
    "chip_array": {"platingThicknessTpl": "vias.plating"},
    "pqfp": {
        "numberOfBondWiresN": "bond_wire.count",
        "metalCoverageForDieFlagCf": "flag.coverage",
        "bondWireLengthOnLeftRightLbwx": "bond_wire.length_x",
        "bondWireLengthOnTopBottomLbwy": "bond_wire.length_y",
    },
    "sop": {"numberOfBondWiresN": "bond_wire.count", "metalCoverageForDieFlagCf": "flag.coverage"},
    "qfn": {
        "bondWireLengthOnLeftRightLbwx": "bond_wire.length_x",
        "bondWireLengthOnTopBottomLbwy": "bond_wire.length_y",
    },
}
MATERIALS = {
    "pbga_wb": {
        "wirebond-bondwire-x": "bondwire_1",
        "wirebond-bondwire-y": "bondwire_2",
        "wirebond-via": "Via",
    },
    "chip_array": {"chip-array-via": "Via"},
    "pqfp": {
        "pqfp-bondwire-x": "bondwire1",
        "pqfp-bondwire-y": "bondwire2",
        "pqfp-die-flag": "die_flag",
    },
    "sop": {
        "sop-bondwire-x": "bondwire1",
        "sop-bondwire-y": "bondwire2",
        "sop-die-flag": "die_flag",
    },
    "qfn": {"qfn-bondwire-x": "bondwirex0", "qfn-bondwire-y": "bondwirey0"},
}


def cases():
    result = []
    for template, fields in FIELDS.items():
        manifest = json.loads((ROOT / template / "xml_variations.json").read_text(encoding="utf-8"))
        for row in manifest["variations"]:
            prop = row["target"]["property"]
            if row["kind"] == "numeric_parameter" and prop in fields:
                result.append(
                    pytest.param(
                        template,
                        fields[prop],
                        row["target"]["value"],
                        ROOT / template / row["artifacts"]["model"],
                        id=f"{template}-{row['variation_id']}",
                    )
                )
    return result


@pytest.mark.parametrize(("template", "field", "value", "path"), cases())
def test_all_eleven_parameter_materials_match_archived_floxml(template, field, value, path):
    model = generate(reference_request(template, {f"{template}.{field}": value}))
    originals = {
        m.findtext("name"): m
        for m in ElementTree.parse(path).getroot().find("./attributes/materials")
    }
    actual = {m.id: m for m in model.materials}
    for identifier, name in MATERIALS[template].items():
        expected = originals[name]
        material = actual[identifier]
        for axis in "xyz":
            value = expected.findtext("conductivity", expected.findtext(f"{axis}_conductivity"))
            assert getattr(material.conductivity, axis) == pytest.approx(float(value), rel=1e-11)
        assert material.density == pytest.approx(float(expected.findtext("density")), rel=1e-11)
        assert material.specific_heat == pytest.approx(
            float(expected.findtext("specific_heat")), rel=1e-11
        )


def test_pqfp_count_truncation_matches_pack_per_side_count():
    baseline = generate(default_request("pqfp"))
    adjacent = generate(
        default_request("pqfp").model_copy(update={"overrides": {"pqfp.bond_wire.count": 33}})
    )
    lower = generate(
        default_request("pqfp").model_copy(update={"overrides": {"pqfp.bond_wire.count": 31}})
    )

    def wire(model):
        return next(m for m in model.materials if m.id == "pqfp-bondwire-x")

    assert wire(baseline).conductivity == wire(adjacent).conductivity
    assert wire(baseline).conductivity != wire(lower).conductivity


def test_component_custom_properties_participate_without_replacing_the_mixture():
    gold = material("gold").model_copy(update={"density": 18000, "specific_heat": 150})
    request = default_request("pbga_wb").model_copy(
        update={
            "custom_materials": [gold],
            "material_assignments": {"group-bond-wires": "gold"},
            "overrides": {"pbga_wb.bond_wire.total": 122},
        }
    )
    model = generate(request)
    wires = [b for b in model.blocks if b.parent_group_id == "group-bond-wires"]
    assert wires and all(b.material_id != "gold" for b in wires)
    mixture = next(m for m in model.materials if m.id == "wirebond-bondwire-x")
    assert "metal=gold;" in mixture.source
    assert mixture.density != gold.density


def test_explicit_generated_material_override_is_preserved():
    base = generate(default_request("pbga_wb"))
    via = next(m for m in base.materials if m.id == "wirebond-via")
    overridden = via.model_copy(update={"density": 4000})
    model = generate(
        default_request("pbga_wb").model_copy(update={"custom_materials": [overridden]})
    )
    assert next(m for m in model.materials if m.id == "wirebond-via").density == 4000


@pytest.mark.parametrize("template", ["pbga_wb", "chip_array"])
def test_plating_larger_than_radius_is_rejected(template):
    with pytest.raises(ValueError, match="plating must not exceed"):
        generate(
            default_request(template).model_copy(
                update={"overrides": {f"{template}.vias.plating": 0.15}}
            )
        )
