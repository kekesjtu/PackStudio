"""Native setter/branch replay verification; opt in on the reviewed installation."""

import os
from pathlib import Path

import pytest

from tools.pack_reference.interactions import InteractionNativePack

INSTALLATION = os.environ.get("PACK_NATIVE_INSTALLATION")
pytestmark = pytest.mark.skipif(
    not INSTALLATION or os.name != "nt",
    reason="requires the reviewed Windows PACK installation",
)


@pytest.fixture(scope="module")
def native():
    return InteractionNativePack(Path(INSTALLATION))


def property_value(snapshot, group, name):
    selected = next(g for g in snapshot["groups"] if g["name"] == group)
    return next(p["value"] for p in selected["properties"] if p["name"] == name)


def test_dataset_edit_is_reset_by_next_probe(native):
    path = native.installation / "flocentral/flopack/pbga_wb/PBGA_121_15X15mm.des"
    baseline = native.probe(path)
    changed = native.probe(path, edits={"numberOfBondWiresNw": 122, "platingThicknessTpl": 0.0275})
    assert property_value(changed, "die", "numberOfBondWiresNw") == "122"
    assert float(property_value(changed, "thermalVias", "platingThicknessTpl")) == 0.0275
    reset = native.probe(path)
    assert property_value(reset, "die", "numberOfBondWiresNw") == property_value(
        baseline, "die", "numberOfBondWiresNw"
    )
    assert property_value(reset, "thermalVias", "platingThicknessTpl") == property_value(
        baseline, "thermalVias", "platingThicknessTpl"
    )


@pytest.mark.parametrize("choice", ["bareDie", "lid", "plate", "encapsulant"])
def test_all_cover_choices_roundtrip(native, choice):
    path = native.installation / "flocentral/flopack/cbga_fc/CBGAFC_49_6X6mm.des"
    snapshot = native.probe(path, wizard={"topCover": choice})
    assert snapshot["wizard"]["topCover"]["enum_label"] == choice
    group = next(g for g in snapshot["groups"] if g["name"] == "topCover")
    assert group["property_details"]["topCover"]["enum_label"] == choice


def test_nested_cover_edit_roundtrip(native):
    path = native.installation / "flocentral/flopack/cbga_fc/CBGAFC_49_6X6mm.des"
    snapshot = native.probe(path, wizard={"topCover": "lid"}, edits={"lidLengthLc": 6.1})
    group = next(g for g in snapshot["groups"] if g["name"] == "topCover")
    lid = next(g for g in group["children"] if "Lid" in g["native_type"])
    assert float(next(p["value"] for p in lid["properties"] if p["name"] == "lidLengthLc")) == 6.1
