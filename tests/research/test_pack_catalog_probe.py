"""Optional live comparison of enriched native data against offline catalog files."""

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
def test_live_snapshot_matches_complete_record(native, family, preset, four_layer):
    path = native.installation / f"flocentral/flopack/{family}/{preset}.des"
    record = {
        "family": family,
        "groups": native.snapshot(path, four_layer),
        "wizard": native.wizard,
    }
    branch = "four_layer" if four_layer else "default"
    assert compiled_branch(record) == PresetCatalog().read_branch(preset, branch)


def test_live_materials_match_raw_values_and_environment_is_restored(native):
    previous = os.environ.get("FLOCENTRALDIR")
    records = read_builtin_materials(native)
    assert os.environ.get("FLOCENTRALDIR") == previous
    assert len(records) == 131
    catalog = MaterialCatalog()
    for record in records:
        assert catalog.read(record["name"])["native_storage"] == record
