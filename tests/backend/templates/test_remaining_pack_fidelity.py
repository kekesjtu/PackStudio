"""Independent native evidence, with explicit project-decision adjustments."""

import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest
from lxml import etree

from packstudio.exporters.floxml import export_floxml
from packstudio.templates.package_library.catalog import generate
from packstudio.templates.package_library.core.parameters import TemplateRequest
from tests.backend.templates.remaining_decisions import decision_geometry
from tests.backend.templates.test_target_pack_fidelity import fingerprint

EVIDENCE = Path(__file__).parents[3] / "docs/validation/remaining-pack-fidelity/evidence.zip"


def evidence_cases():
    with ZipFile(EVIDENCE) as archive:
        return json.loads(archive.read("cases.json"))


@pytest.mark.parametrize("case", evidence_cases(), ids=lambda c: c["id"])
def test_remaining_native_cuboids_and_constituents(case):
    with ZipFile(EVIDENCE) as archive:
        original = decision_geometry(
            ET.fromstring(archive.read(case["id"] + ".xml")), case["request"]["template_id"]
        )
    model = generate(TemplateRequest.model_validate(case["request"]))
    exported = ET.fromstring(export_floxml(model))
    expected, actual = fingerprint(original), fingerprint(exported)
    assert set(expected) == set(actual), {
        "missing": {k: expected[k] for k in set(expected) - set(actual)},
        "extra": {k: actual[k] for k in set(actual) - set(expected)},
    }
    for shape, entries in expected.items():
        remaining = actual[shape].copy()
        for name, properties in entries:
            match = next(
                (
                    item
                    for item in remaining
                    if item[1] == pytest.approx(properties, rel=1e-10, abs=1e-8)
                ),
                None,
            )
            assert match is not None, (case["id"], name, properties, remaining)
            remaining.remove(match)
        assert not remaining
    for tag in ("region", "monitor_point", "grid_constraint_att"):
        expected_items = {e.findtext("name"): e for e in original.findall(".//" + tag)}
        actual_items = {e.findtext("name"): e for e in exported.findall(".//" + tag)}
        assert expected_items.keys() == actual_items.keys()
        for name, expected_item in expected_items.items():
            for old, new in zip(expected_item.iter(), actual_items[name].iter(), strict=True):
                assert old.tag == new.tag
                if old.text and old.text.strip():
                    try:
                        assert float(new.text) == pytest.approx(float(old.text), abs=1e-12)
                    except ValueError:
                        assert old.text == new.text
    assert original.findtext("localized_grid") == exported.findtext("localized_grid")
    native_power = sum(float(s.findtext("power")) for s in original.findall(
        "attributes/sources/source_att"))
    assert native_power == pytest.approx(sum(s.power_w for s in model.heat_sources))


def test_remaining_evidence_provenance_and_export_schema():
    schema = etree.XMLSchema(etree.parse(str(
        Path(__file__).parents[3] / "output_format/floxml/xmlSchema.xsd")))
    with ZipFile(EVIDENCE) as archive:
        run = json.loads(archive.read("run.json"))
        assert run["status"] == "success" and all(run["checks"].values())
        for identifier, digest in run["exports"].items():
            assert hashlib.sha256(archive.read(identifier + ".xml")).hexdigest() == digest
        for case in evidence_cases():
            model = generate(TemplateRequest.model_validate(case["request"]))
            schema.assertValid(etree.fromstring(export_floxml(model)))
