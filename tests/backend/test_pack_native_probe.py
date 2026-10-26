import os
from pathlib import Path

import pytest

from packstudio.preset_catalog import PresetCatalog
from tools.pack_reference.native import VERIFIED_BINARIES, NativePack


def properties(record: dict) -> dict:
    return {p["name"]: p["value"] for group in record["groups"] for p in group["properties"]}


def test_catalog_keeps_native_conditional_branches() -> None:
    catalog = PresetCatalog()
    assert len(catalog.list_ids()) == 342
    for preset in ["PBGA_121_15X15mm", "ChipArray_24_4X4mm_0_8"]:
        record = catalog.read(preset)
        assert set(record["branches"]) == {"default", "four_layer"}
        group = "packageSubstrate" if preset.startswith("PBGA") else "overallPackage"
        for branch, thickness in [("default", 0.36), ("four_layer", 0.56)]:
            prop = record["branches"][branch]["groups"][group]["properties"]["substrateThicknessA2"]
            assert prop["value"] == thickness


@pytest.mark.skipif(os.name != "nt", reason="Windows native ABI")
def test_unreviewed_dll_is_rejected_before_loading(tmp_path, monkeypatch) -> None:
    directory = tmp_path / "WinXP/bin"
    directory.mkdir(parents=True)
    first = next(iter(VERIFIED_BINARIES))
    (directory / first).write_bytes(b"another build must not be loaded")

    def unexpected_load(*args, **kwargs):
        pytest.fail("an unreviewed DLL was loaded")

    monkeypatch.setattr("ctypes.CDLL", unexpected_load)
    with pytest.raises(ValueError, match="unreviewed PACK binary"):
        NativePack(tmp_path)


@pytest.mark.parametrize(
    "family,preset,four_layer,thickness,vias",
    [
        ("pbga_wb", "PBGA_121_15X15mm", False, "0.36", "5"),
        ("pbga_wb", "PBGA_121_15X15mm", True, "0.56", "3"),
        ("pbga_wb", "PBGA_352_35X35mm", False, "0.56", "5"),
        ("pbga_wb", "PBGA_352_35X35mm", True, "0.56", "3"),
        ("pbga_fc", "PBGAFC_49_6X6mm", False, "1.15", None),
    ],
)
def test_native_wizard_branch(family, preset, four_layer, thickness, vias) -> None:
    installation = os.environ.get("PACK_NATIVE_INSTALLATION")
    if os.name != "nt" or not installation:
        pytest.skip("set PACK_NATIVE_INSTALLATION to run installed PACK integration checks")
    native = NativePack(Path(installation))
    source = native.installation / "flocentral/flopack" / family / f"{preset}.des"
    groups = native.snapshot(source, four_layer)
    values = properties({"groups": groups})
    assert values["substrateThicknessA2"] == thickness
    assert values["maxPower"] is None
    if vias:
        assert values["numberOfThermalViasInXNVx"] == vias
        assert values["numberOfThermalViasInYNVy"] == vias
        assert values["viaPitchEv"] == values["ballPitchE"]
