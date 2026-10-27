"""Overlaps are model warnings; contact and invalid references remain distinct."""

import json

import pytest
from lxml import etree

from packstudio.domain.model import PackageModel
from packstudio.exporters.floxml import export_floxml
from packstudio.templates.package_library.catalog import default_request, generate


def overlapping_payload():
    payload = generate(default_request("bare_die")).model_dump()
    first = payload["blocks"][0]
    payload["blocks"].append({**first, "id": "insert", "name": "Insert"})
    next(g for g in payload["groups"] if g["id"] == first["parent_group_id"])["block_ids"].append(
        "insert"
    )
    return payload


def test_overlap_preserves_both_blocks_and_exports_warning():
    model = PackageModel.model_validate(overlapping_payload())
    assert len(model.blocks) == 2
    assert len(model.warnings) == 1
    assert "insert" in model.warnings[0]
    exported = etree.fromstring(export_floxml(model))
    assert len(exported.findall(".//cuboid")) == 2
    assert json.loads(exported.findtext("notes"))["warnings"] == model.warnings
    assert PackageModel.model_validate_json(model.model_dump_json()).warnings == model.warnings


def test_face_contact_clears_stale_overlap_warning():
    payload = overlapping_payload()
    first, second = payload["blocks"]
    second["origin"] = {**first["origin"], "x": first["origin"]["x"] + first["size"]["x"]}
    payload["warnings"] = ["stale warning"]
    assert PackageModel.model_validate(payload).warnings == []


def test_overlap_permission_keeps_material_references_validated():
    payload = overlapping_payload()
    payload["blocks"][1]["material_id"] = "missing"
    with pytest.raises(ValueError, match="unknown material"):
        PackageModel.model_validate(payload)
