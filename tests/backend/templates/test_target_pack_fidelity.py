"""Compare public generation and exports to independently captured native cuboids."""

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

EVIDENCE = Path(__file__).parents[3] / "docs/validation/target-pack-fidelity/evidence.zip"


def evidence_cases():
    with ZipFile(EVIDENCE) as archive:
        return json.loads(archive.read("cases.json"))


@pytest.mark.parametrize("case", evidence_cases(), ids=lambda case: case["id"])
def test_native_geometry_material_and_grid_fidelity(case):
    with ZipFile(EVIDENCE) as archive:
        expected = ET.fromstring(archive.read(case["id"] + ".xml"))
    compare_native(expected, case["request"])


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
