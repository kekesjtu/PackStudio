"""Metal depth contract and disconnect alignment against native probe evidence."""

import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from lxml import etree

from packstudio.exporters.floxml import export_floxml
from packstudio.templates.package_library.catalog import definition, generate
from packstudio.templates.package_library.core.parameters import TemplateRequest
from tests.backend.templates.native_references import product_cases, verify_fingerprints
from tools.floscript.des import read_des

ROOT = Path(__file__).parents[3]


def cases():
    result = []
    for case in product_cases():
        if case["template"] == "pbga_wb" and case["id"].startswith("metal-depth-"):
            data = read_des(case["directory"] / "input.des")
            result.append(
                {
                    **case,
                    "inputs_mm": {
                        "top": float(data["tz1"]),
                        "inner": float(data["tz2"]),
                        "depth": float(data["z2"]),
                    },
                }
            )
    assert len(result) == 6
    return result


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
    native = ET.parse(case["directory"] / "model.xml").getroot()
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
    for case in cases():
        directory, inputs = case["directory"], case["inputs_mm"]
        assert all(verify_fingerprints(directory)["checks"].values())
        readback = read_des(directory / "model.des")
        assert float(readback["tz1"]) == inputs["top"]
        assert float(readback["tz2"]) == inputs["inner"]
        assert float(readback["z2"]) == inputs["depth"]
        cuboids = {
            b.findtext("name"): b for b in ET.parse(directory / "model.xml").findall(".//cuboid")
        }
        offset = (
            float(cuboids["discon2"].findtext("position/z"))
            - float(cuboids["trace_1"].findtext("position/z"))
        ) * 1000
        assert offset == pytest.approx(2 * inputs["top"] - inputs["inner"])
