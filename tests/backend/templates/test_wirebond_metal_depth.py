"""Metal depth contract and disconnect alignment against native probe evidence."""

import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest
from lxml import etree

from packstudio.exporters.floxml import export_floxml
from packstudio.templates.package_library.catalog import definition, generate
from packstudio.templates.package_library.core.parameters import TemplateRequest

ROOT = Path(__file__).parents[3]
EVIDENCE = ROOT / "docs/validation/wb-metal-depth/evidence.zip"


def cases():
    with ZipFile(EVIDENCE) as archive:
        return json.loads(archive.read("cases.json"))


def request_for(case, mode):
    inputs = case["inputs_mm"]
    request = TemplateRequest(
        template_id="pbga_wb",
        overrides={
            "pbga_wb.substrate.layers": "4-Layer",
            "pbga_wb.vias.modeling": mode,
        },
    )
    rows = definition("pbga_wb").validate_request(request).table("metal.layers")
    rows[0]["thickness"] = inputs["top"]
    rows[1].update(depth=inputs["depth"], thickness=inputs["inner"], disconnect=True)
    rows[2]["disconnect"] = False
    return request.model_copy(
        update={
            "overrides": {
                **request.overrides,
                "pbga_wb.metal.layers": json.dumps(rows),
            }
        }
    )


@pytest.mark.parametrize("case", cases(), ids=lambda c: c["id"])
@pytest.mark.parametrize("mode", ["discreteCuboids", "orthotropicCuboid", "isotropicCuboid"])
def test_inner_copper_and_disconnect_follow_native_depth_contract(case, mode):
    with ZipFile(EVIDENCE) as archive:
        native = ET.fromstring(archive.read(case["id"] + ".xml"))
    native_disconnect = next(
        b for b in native.findall(".//cuboid") if b.findtext("name") == "discon2"
    )
    expected_z = float(native_disconnect.findtext("position/z")) * 1000
    expected_thickness = float(native_disconnect.findtext("size/z")) * 1000
    model = generate(request_for(case, mode))
    copper = next(b for b in model.blocks if b.id == "trace-1-part-1")
    disconnect = next(b for b in model.blocks if b.id == "disconnect-1-part-1")
    assert copper.origin.z == disconnect.origin.z == pytest.approx(expected_z)
    assert copper.size.z == disconnect.size.z == pytest.approx(expected_thickness)
    assert copper.max_z == pytest.approx(1.16 - case["inputs_mm"]["depth"])
    exported = etree.fromstring(export_floxml(model))
    for block in (copper, disconnect):
        element = next(e for e in exported.findall(".//cuboid") if e.findtext("name") == block.id)
        assert float(element.findtext("position/z")) == pytest.approx(expected_z * 0.001)
        assert float(element.findtext("size/z")) == pytest.approx(expected_thickness * 0.001)
    etree.XMLSchema(etree.parse(str(ROOT / "output_format/floxml/xmlSchema.xsd"))).assertValid(
        exported
    )


def test_inner_depth_and_thickness_apply_to_layers_without_disconnect():
    case = cases()[1]
    request = request_for(case, "discreteCuboids")
    rows = json.loads(request.overrides["pbga_wb.metal.layers"])
    rows[2].update(depth=0.3, thickness=0.05)
    request = request.model_copy(
        update={
            "overrides": {
                **request.overrides,
                "pbga_wb.metal.layers": json.dumps(rows),
            }
        }
    )
    model = generate(request)
    copper = next(b for b in model.blocks if b.id == "trace-2-part-1")
    assert (copper.origin.z, copper.max_z) == pytest.approx((0.81, 0.86))
    assert not any(b.id.startswith("disconnect-2-") for b in model.blocks)


def test_original_probe_evidence_preserves_parameters_and_native_offset():
    with ZipFile(EVIDENCE) as archive:
        run = json.loads(archive.read("run.json"))
        assert run["status"] == "success" and all(run["checks"].values())
        for identifier, digest in run["exports"].items():
            assert hashlib.sha256(archive.read(identifier + ".xml")).hexdigest() == digest
        results = json.loads(archive.read("results.json"))
        for row in results:
            assert float(row["readback"]["tz1"]) == row["top"]
            assert float(row["readback"]["tz2"]) == row["inner"]
            assert float(row["readback"]["z2"]) == row["depth"]
            assert row["discon2"][0] - row["trace_1"][0] == pytest.approx(
                2 * row["top"] - row["inner"]
            )
