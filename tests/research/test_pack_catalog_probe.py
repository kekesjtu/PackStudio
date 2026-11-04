"""Optional live comparisons of native die parameters and material records."""

import os
from pathlib import Path

import pytest

from tools.data_library.material_catalog import MaterialCatalog
from tools.data_library.preset_catalog import PresetCatalog
from tools.pack_reference.catalog import compiled_branch
from tools.pack_reference.materials import read_builtin_materials
from tools.pack_reference.native_details import DetailedNativePack

INSTALLATION = os.environ.get("PACK_NATIVE_INSTALLATION")
pytestmark = pytest.mark.skipif(
    not INSTALLATION or os.name != "nt", reason="requires the reviewed Windows PACK installation"
)


@pytest.fixture(scope="module")
def native():
    return DetailedNativePack(Path(INSTALLATION))


@pytest.mark.parametrize(
    ("family", "preset", "four_layer"),
    [
        ("pbga_wb", "PBGA_352_35X35mm", False),
        ("pbga_wb", "PBGA_121_15X15mm", True),
        ("pbga_fc", "PBGAFC_49_6X6mm", False),
        ("chip_array", "ChipArray_48_6X6mm_0_5", False),
        ("tsop_conv", "TSSOP_10_3x3", False),
        ("QFN", "QFN_10X10_44", False),
    ],
)
def test_live_die_parameters_match_internal_preset(native, family, preset, four_layer):
    path = native.installation / f"flocentral/flopack/{family}/{preset}.des"
    record = {
        "family": family,
        "groups": native.snapshot(path, four_layer),
        "wizard": native.wizard,
    }
    branch = "four_layer" if four_layer else "default"
    raw = compiled_branch(record)
    internal = PresetCatalog().read_branch(preset, branch)
    # Compare independently named physical quantities across the native/runtime boundary.
    die = raw["groups"]["die"]["properties"]
    for key, prop in [("die.length", "dieLengthLd"), ("die.width", "dieWidthWd"),
                      ("die.thickness", "dieThicknessTd"), ("die.power", "packagePower")]:
        assert internal["values"][key] == die[prop]["value"]
    assert internal["material_assignments"]["group-die"] == "silicon"


def test_live_material_properties_and_environment_is_restored(native):
    previous = os.environ.get("FLOCENTRALDIR")
    records = read_builtin_materials(native)
    assert os.environ.get("FLOCENTRALDIR") == previous
    catalog = MaterialCatalog()
    for record in records:
        material = catalog.read(record["name"])
        assert material["density_kg_m3"] == record["density_kg_m3"]
        assert material["specific_heat_j_kg_k"] == record["specific_heat_j_kg_k"]
        assert material["conduct_type"] == record["conductivity_type"]
        if record["conductivity_type"] == 2:
            for axis in ("x", "y", "z"):
                assert material[f"k{axis}_w_m_k"] == record[f"k{axis}_w_m_k"]
        else:
            assert material["conductivity_w_m_k"] == record["conductivity_w_m_k"]
            if record["conductivity_type"] == 1:
                assert material["conductivity_coefficient"] == record["conductivity_coefficient"]
                assert material["conductivity_reference_temperature"] == record[
                    "conductivity_reference_temperature"
                ]
