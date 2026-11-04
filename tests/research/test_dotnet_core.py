"""Explicit CLI invocation, diagnostics, and research request protocol."""

import os
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from tools import dotnet_core


def test_missing_binary_requires_explicit_build(monkeypatch, tmp_path):
    monkeypatch.delenv("PACKSTUDIO_CLI_BINARY", raising=False)
    monkeypatch.setattr(dotnet_core, "BINARY", tmp_path / "missing.dll")

    def unexpected_build(*args, **kwargs):
        raise AssertionError("research invocation must not build")

    monkeypatch.setattr(subprocess, "run", unexpected_build)
    with pytest.raises(FileNotFoundError, match="build.ps1 -Target Cli"):
        dotnet_core.resolve_values({"template_id": "bare_die"})


def test_existing_binary_runs_without_build_and_reports_failures(monkeypatch, tmp_path):
    binary = tmp_path / "cli.dll"
    binary.touch()
    monkeypatch.setenv("PACKSTUDIO_CLI_BINARY", str(binary))
    monkeypatch.setattr(dotnet_core, "ROOT", tmp_path)
    calls = []

    def fail(command, **kwargs):
        calls.append(command)
        raise subprocess.CalledProcessError(
            1, command, output="request context", stderr="invalid field"
        )

    monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises(RuntimeError, match="request context\ninvalid field"):
        dotnet_core.resolve_values({"template_id": "bare_die"})
    assert len(calls) == 1
    assert calls[0][:3] == ["dotnet", str(binary), "values"]


@pytest.fixture
def cli():
    binary = os.environ.get("PACKSTUDIO_CLI_BINARY")
    if not binary or not Path(binary).is_file():
        pytest.skip("set PACKSTUDIO_CLI_BINARY to an explicitly built CLI for integration tests")
    return dotnet_core


def test_request_preserves_false_null_and_object_overrides(cli):
    values = cli.resolve_values({
        "template_id": "pbga_wb",
        "overrides": {
            "pbga_wb.bga.center_solder_enabled": False,
            "pbga_wb.bga.center_solder_rows": None,
            "pbga_wb.vias.configuration": {
                "removal_enabled": True, "removal_rows": 1, "removal_columns": 2,
            },
        },
    })
    assert values["bga.center_solder_enabled"] is False
    assert values["bga.center_solder_rows"] is None
    assert values["vias.configuration"]["removal_columns"] == 2


def test_request_rejects_unknown_protocol_fields_and_nested_leaf_paths(cli):
    with pytest.raises(RuntimeError, match="extra"):
        cli.resolve_values({"template_id": "bare_die", "extra": True})
    with pytest.raises(RuntimeError, match="vias.configuration.removal_enabled"):
        cli.resolve_values({
            "template_id": "pbga_wb",
            "overrides": {"pbga_wb.vias.configuration.removal_enabled": True},
        })


def test_footprint_override_selects_preset(cli):
    family = next(f for f in cli.invoke("catalog", {}) if f["id"] == "chip_array")
    preset = family["presets"][-1]
    values = cli.resolve_values({
        "template_id": "chip_array", "overrides": {"chip_array.footprint.size": preset},
    })
    assert values["footprint.size"] == preset


def test_batch_request_initializes_four_layer_geometry(cli):
    model = cli.export_floxml({
        "template_id": "chip_array",
        "overrides": {
            "chip_array.trace.solid_thickness": 0.05,
            "chip_array.substrate.thickness": 0.75,
            "chip_array.substrate.layers": "4-Layer",
        },
    })
    assert ET.fromstring(model).find("geometry") is not None
