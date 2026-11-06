"""Explicit CLI invocation, diagnostics, and research request protocol."""

import json
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
            "bga.center_solder_enabled": False,
            "bga.center_solder_rows": None,
            "vias.configuration": {
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
            "overrides": {"vias.configuration.removal_enabled": True},
        })
    with pytest.raises(RuntimeError, match=r"pbga_wb\.die\.power"):
        cli.resolve_values({"template_id": "pbga_wb", "overrides": {"pbga_wb.die.power": 2.5}})
    with pytest.raises(RuntimeError, match=r"footprint\.size"):
        cli.resolve_values({"template_id": "pbga_wb", "overrides": {"footprint.size": "PBGA_121_15X15mm"}})


def test_footprint_override_selects_preset(cli):
    family = next(f for f in cli.invoke("catalog", {}) if f["id"] == "chip_array")
    preset = family["presets"][-1]
    values = cli.resolve_values({
        "template_id": "chip_array", "footprint.size": preset,
    })
    index_path = cli.ROOT / "runtime_data/presets/index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    preset_path = cli.ROOT / "runtime_data/presets" / index["presets"][preset]["file"]
    document = json.loads(preset_path.read_text(encoding="utf-8"))
    assert "footprint.size" not in values
    assert values["die.length"] == document["Values"]["die.length"]
    assert values["package.length"] == document["Values"]["package.length"]


def test_batch_request_initializes_four_layer_geometry(cli):
    model = cli.export_model({
        "template_id": "chip_array",
        "overrides": {
            "trace.solid_thickness": 0.05,
            "substrate.thickness": 0.75,
            "substrate.layers": "4-Layer",
        },
    })
    assert ET.fromstring(model).find("group/block") is not None


def test_creation_preserves_invalid_input_until_generation(cli):
    request = {
        "template_id": "bare_die",
        "overrides": {
            "die.length": None,
            "die.width": 0,
            "bumps.enabled": False,
        },
    }
    values = cli.resolve_values(request)
    assert values["die.length"] is None
    assert values["die.width"] == 0
    assert values["bumps.enabled"] is False
    with pytest.raises(RuntimeError, match="input.required"):
        cli.export_model(request)


def test_material_request_migrates_legacy_type_and_respects_explicit_type(cli):
    material = {
        "id": "silicon", "name": "Custom silicon",
        "conductivity": {"x": 12, "y": 12, "z": 12},
        "density": 2000, "specific_heat": 700,
    }
    for conductivity_type, expected_type in [
        (None, "isotropic"),
        (2, "orthotropic"),
        (1, "temperature_dependent"),
    ]:
        submitted = dict(material)
        if conductivity_type is not None:
            submitted["conduct_type"] = conductivity_type
        if conductivity_type == 1:
            submitted.update(conductivity_coefficient=0, conductivity_reference_temperature_c=-20)
        model = cli.export_model({"template_id": "bare_die", "custom_materials": [submitted]})
        definition = ET.fromstring(model).find("materials/material")
        assert definition.attrib["type"] == expected_type
        assert definition.attrib["name"] == "Custom silicon"
        assert definition.attrib["id"] != "silicon"
    with pytest.raises(RuntimeError, match="conduct_type"):
        cli.export_model({
            "template_id": "bare_die", "custom_materials": [dict(material, conduct_type=0.5)],
        })
    with pytest.raises(RuntimeError, match="material_assignments"):
        cli.resolve_values({"template_id": "bare_die", "material_assignments": {"group-die": None}})
