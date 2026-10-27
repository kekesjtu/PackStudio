"""Compare public generation and exports to independently captured native cuboids."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest
from lxml import etree

from packstudio.exporters.floxml import export_floxml
from packstudio.templates.package_library.catalog import generate
from packstudio.templates.package_library.core.parameters import TemplateRequest

EVIDENCE = Path(__file__).parents[3] / "docs/validation/target-pack-fidelity/evidence.zip"


def evidence_cases():
    with ZipFile(EVIDENCE) as archive:
        return json.loads(archive.read("cases.json"))


def fingerprint(root):
    materials = {}
    for item in root.findall("attributes/materials/*"):
        scalar = item.findtext("conductivity")
        if scalar is not None:
            tensor = [float(scalar)] * 3
        elif item.find("in_plane_conductivity") is not None:
            tensor = [float(item.findtext("in_plane_conductivity"))] * 2 + [
                float(item.findtext("normal_conductivity"))
            ]
        else:
            tensor = [float(item.findtext(f"{a}_conductivity")) for a in "xyz"]
        materials[item.findtext("name")] = (
            *tensor,
            float(item.findtext("density")),
            float(item.findtext("specific_heat")),
        )
    groups = defaultdict(list)

    def visit(geometry, offset=(0, 0, 0), inherited=None):
        for item in geometry:
            if item.tag not in {"assembly", "cuboid"}:
                continue
            origin = tuple(
                float(item.findtext(f"position/{a}", "0")) + offset[i] for i, a in enumerate("xyz")
            )
            material = item.findtext("material") or inherited
            if item.tag == "assembly":
                visit(item.find("geometry"), origin, material)
            else:
                key = tuple(round(x * 1000, 8) for x in origin) + tuple(
                    round(float(item.findtext(f"size/{a}")) * 1000, 8) for a in "xyz"
                )
                groups[key].append((item.findtext("name"), materials.get(material)))

    visit(root.find("geometry"))
    return groups


@pytest.mark.parametrize("case", evidence_cases(), ids=lambda case: case["id"])
def test_native_geometry_material_and_grid_fidelity(case):
    with ZipFile(EVIDENCE) as archive:
        expected = ET.fromstring(archive.read(case["id"] + ".xml"))
    model = generate(TemplateRequest.model_validate(case["request"]))
    actual = ET.fromstring(export_floxml(model))
    original, generated = fingerprint(expected), fingerprint(actual)
    assert set(original) == set(generated), {
        "missing": set(original) - set(generated),
        "extra": set(generated) - set(original),
    }
    for shape, expected_materials in original.items():
        remaining = generated[shape].copy()
        for name, material in expected_materials:

            def matches(item, material=material, name=name):
                if material is None:
                    return item[1] is None
                if item[1] is None:
                    return False
                start = 2 if case["id"].startswith("bare-bumped") and "bump" in name else 0
                return item[1][start:] == pytest.approx(material[start:], rel=1e-10, abs=1e-8)

            match = next((item for item in remaining if matches(item)), None)
            assert match is not None, (case["id"], shape, expected_materials, remaining)
            remaining.remove(match)
        assert not remaining
    for original_grid, actual_grid in zip(
        expected.findall("attributes/grid_constraints/grid_constraint_att"),
        actual.findall("attributes/grid_constraints/grid_constraint_att"),
        strict=True,
    ):
        for old, new in zip(original_grid.iter(), actual_grid.iter(), strict=True):
            assert old.tag == new.tag
            if old.text and old.text.strip():
                try:
                    assert float(old.text) == pytest.approx(float(new.text), abs=1e-12)
                except ValueError:
                    assert old.text == new.text
    assert expected.findtext("localized_grid") == actual.findtext("localized_grid")
    for tag in ("region", "monitor_point"):

        def auxiliary(root, tag=tag):
            return {
                item.findtext("name"): tuple(
                    float(item.findtext(f"position/{axis}", "0")) for axis in "xyz"
                )
                + tuple(float(item.findtext(f"size/{axis}", "0")) for axis in "xyz")
                for item in root.findall(".//" + tag)
            }

        original_aux, generated_aux = auxiliary(expected), auxiliary(actual)
        assert original_aux.keys() == generated_aux.keys()
        for name, coordinates in original_aux.items():
            assert generated_aux[name] == pytest.approx(coordinates, abs=1e-12)
    original_laws = expected.findall("attributes/materials/temperature_dependant_material_att")
    generated_laws = actual.findall("attributes/materials/temperature_dependant_material_att")
    assert sorted(
        tuple(float(e.findtext(k)) for k in ("conductivity", "coeff", "tref"))
        for e in original_laws
    ) == pytest.approx(
        sorted(
            tuple(float(e.findtext(k)) for k in ("conductivity", "coeff", "tref"))
            for e in generated_laws
        )
    )
    assert sum(
        float(s.findtext("power")) for s in expected.findall("attributes/sources/source_att")
    ) == pytest.approx(sum(s.power_w for s in model.heat_sources))


def test_evidence_provenance_and_export_schema():
    with ZipFile(EVIDENCE) as archive:
        for name in ("run.json", "advanced-run.json"):
            run = json.loads(archive.read(name))
            assert run["status"] == "success"
            assert all(run["checks"].values())
            for identifier, digest in run["exports"].items():
                assert hashlib.sha256(archive.read(identifier + ".xml")).hexdigest() == digest
    schema = etree.XMLSchema(
        etree.parse(str(Path(__file__).parents[3] / "output_format/floxml/xmlSchema.xsd"))
    )
    for case in evidence_cases():
        schema.assertValid(
            etree.fromstring(
                export_floxml(generate(TemplateRequest.model_validate(case["request"])))
            )
        )
