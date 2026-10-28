"""Public model fidelity against versioned, independently exported native points."""

import json
from pathlib import Path

import pytest
from lxml import etree

from packstudio.exporters.floxml import export_floxml
from packstudio.templates.package_library.catalog import generate
from packstudio.templates.package_library.core.parameters import TemplateRequest
from tests.backend.templates.native_references import ROOT, product_cases, verify_fingerprints
from tools.pack_sweep.compare import compare_model


@pytest.fixture(scope="module")
def schema():
    return etree.XMLSchema(
        etree.parse(str(Path(__file__).parents[3] / "output_format/floxml/xmlSchema.xsd"))
    )


@pytest.mark.parametrize("case", product_cases(), ids=lambda c: c["template"] + "/" + c["id"])
def test_native_geometry_material_power_and_grid_fidelity(case, schema):
    directory = case["directory"]
    assert all(verify_fingerprints(directory)["checks"].values())
    schema.assertValid(etree.parse(str(directory / "model.xml")))
    compare_model(directory / "model.xml", case["request"])
    model = generate(TemplateRequest.model_validate(case["request"]))
    schema.assertValid(etree.fromstring(export_floxml(model)))


def test_reference_index_covers_every_point_and_preserves_native_schema_errors(schema):
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    directories = {p.parent for p in ROOT.glob("template/*/*/case.json")}
    assert directories == {ROOT / relative for relative in index["points"]}
    errors = []
    for directory in sorted(directories):
        run = verify_fingerprints(directory)
        try:
            schema.assertValid(etree.parse(str(directory / "model.xml")))
        except etree.DocumentInvalid:
            assert not run["checks"]["floxml_schema"] and run["native_schema_error"]
            errors.append(directory)
        else:
            assert run["checks"]["floxml_schema"]
        assert (directory / "validate.py").is_file()
    assert len(errors) == 7
    assert all(p.name == "opt_v2_c001_outlinetype_nonstandardoutline" for p in errors)
    for image in json.loads((ROOT / "screenshots.json").read_text(encoding="utf-8")):
        import hashlib

        assert hashlib.sha256((ROOT / image["path"]).read_bytes()).hexdigest() == image["sha256"]
