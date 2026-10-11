import json
import os
from pathlib import Path

import pytest

from tools.audit_pack_native_defaults import (
    DIRECTORY,
    properties,
    rule_audit,
    source_audit,
    xml_audit,
)
from tools.pack_native import VERIFIED_BINARIES, NativePack


def test_archived_native_snapshots_match_sources_rules_and_floxml() -> None:
    records = json.loads((DIRECTORY / "native_defaults.json").read_text())["records"]
    four_layer = json.loads((DIRECTORY / "native_defaults_4layer.json").read_text())["records"]
    assert len(records) == 342
    assert len(four_layer) == 74
    assert source_audit(records)["die_dimensions_checked"] == 1026
    assert rule_audit(records, four_layer)["conditional_rule_assertions"] == 512
    assert len(xml_audit(records, four_layer)) == 6
    for record in records + four_layer:
        for group in record["groups"]:
            for prop in group["properties"]:
                assert (prop["value"] is None) == (prop["native_state"] == 0)


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
