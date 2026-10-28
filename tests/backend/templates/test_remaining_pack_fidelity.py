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
from tools.pack_sweep.compare import compare_native

EVIDENCE = Path(__file__).parents[3] / "docs/validation/remaining-pack-fidelity/evidence.zip"


def evidence_cases():
    with ZipFile(EVIDENCE) as archive:
        return json.loads(archive.read("cases.json"))


@pytest.mark.parametrize("case", evidence_cases(), ids=lambda c: c["id"])
def test_remaining_native_cuboids_and_constituents(case):
    with ZipFile(EVIDENCE) as archive:
        original = ET.fromstring(archive.read(case["id"] + ".xml"))
    compare_native(original, case["request"])


def test_remaining_evidence_provenance_and_export_schema():
    schema = etree.XMLSchema(
        etree.parse(str(Path(__file__).parents[3] / "output_format/floxml/xmlSchema.xsd"))
    )
    with ZipFile(EVIDENCE) as archive:
        run = json.loads(archive.read("run.json"))
        assert run["status"] == "success" and all(run["checks"].values())
        for identifier, digest in run["exports"].items():
            assert hashlib.sha256(archive.read(identifier + ".xml")).hexdigest() == digest
        for case in evidence_cases():
            model = generate(TemplateRequest.model_validate(case["request"]))
            schema.assertValid(etree.fromstring(export_floxml(model)))
