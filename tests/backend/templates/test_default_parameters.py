import hashlib
import json
import runpy
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import packstudio.default_parameters as library
from packstudio.api.app import create_app
from packstudio.templates.package_library.catalog import (
    default_request,
    definitions,
    generate,
    schema,
)
from packstudio.templates.package_library.core.materials import production_materials

ROOT = Path(__file__).resolve().parents[3]


def test_all_342_records_are_lossless_and_checksummed() -> None:
    snapshot = json.loads((ROOT / "flotherm_pack_data/installation/presets.json").read_text())
    original = {item["path"]: item for item in snapshot["records"]}
    directory = library.library_directory()
    manifest = json.loads((directory / "manifest.json").read_text())
    snapshot_bytes = (ROOT / "flotherm_pack_data/installation/presets.json").read_bytes()
    assert (
        manifest["source_snapshot_sha256"]
        == hashlib.sha256(snapshot_bytes.replace(b"\r\n", b"\n")).hexdigest()
    )
    paths = []
    for family in manifest["families"]:
        path = directory / family["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == family["sha256"]
        payload = json.loads(path.read_text())
        assert len(payload["records"]) == family["count"]
        for record in payload["records"]:
            paths.append(record["source_path"])
            source = original[record["source_path"]]
            assert record["raw_fields"] == source["fields"]
            assert record["source_sha256"] == source["sha256"]
            assert record["id"] == Path(source["path"]).stem
            assert set(record["values"]) == set(source["fields"])
            for key, raw in source["fields"].items():
                if raw == "":
                    assert record["values"][key] is None
                elif isinstance(record["values"][key], int | float):
                    assert float(record["values"][key]) == float(raw)
                else:
                    assert record["values"][key] == raw
    assert len(paths) == len(set(paths)) == manifest["record_count"] == 342
    assert set(paths) == set(original)


@pytest.fixture
def isolated_library(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    copied = tmp_path / "default_parameters"
    shutil.copytree(library.library_directory(), copied)
    monkeypatch.setattr(library, "library_directory", lambda: copied)
    library._read.cache_clear()
    definitions.cache_clear()
    production_materials.cache_clear()
    yield copied
    library._read.cache_clear()
    definitions.cache_clear()
    production_materials.cache_clear()


def edit_json(path: Path, update) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    update(payload)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_json_changes_drive_geometry_and_schema(isolated_library: Path) -> None:
    def update(payload):
        field = next(item for item in payload["fields"] if item["key"] == "die.thickness")
        field["default"] = 0.28

    edit_json(isolated_library / "templates/flip_chip_cbga.json", update)
    model = generate(default_request("flip_chip_cbga"))
    die = next(block for block in model.blocks if block.name == "Silicon die")
    assert die.size.z == pytest.approx(0.28)
    fields = [item for step in schema("flip_chip_cbga")["steps"] for item in step["fields"]]
    assert (
        next(item for item in fields if item["property_name"] == "die.thickness")["default"] == 0.28
    )


def test_source_preset_values_are_read_at_runtime(isolated_library: Path) -> None:
    def update(payload):
        record = next(item for item in payload["records"] if item["id"] == "CBGAFC_49_6X6mm")
        record["values"]["Ld"] = 1.9

    edit_json(isolated_library / "flotherm/cbga_fc.json", update)
    model = generate(default_request("flip_chip_cbga"))
    die = next(block for block in model.blocks if block.name == "Silicon die")
    assert die.size.x == 1.9


def test_material_and_request_defaults_come_from_json(isolated_library: Path) -> None:
    def update_material(payload):
        payload["materials"][1]["conductivity"] = {"x": 123, "y": 123, "z": 123}

    edit_json(isolated_library / "materials.json", update_material)
    edit_json(
        isolated_library / "request.json", lambda data: data["mesh"].update(resolution="fine")
    )
    model = generate(default_request("bare_die"))
    assert model.materials[0].conductivity.x == 123
    assert model.metadata["mesh_resolution"] == "fine"


@pytest.mark.parametrize("failure", ["missing", "version", "nonfinite"])
def test_invalid_library_fails_without_hardcoded_fallback(
    isolated_library: Path, failure: str
) -> None:
    path = isolated_library / "templates/bare_die.json"
    if failure == "missing":
        path.unlink()
    elif failure == "version":
        edit_json(path, lambda payload: payload.update(schema_version="unsupported"))
    else:

        def update(payload):
            next(item for item in payload["fields"] if item["key"] == "die.thickness")[
                "default"
            ] = float("nan")

        edit_json(path, update)
    with pytest.raises(ValueError):
        generate(default_request("bare_die"))


def test_request_defaults_are_not_shared_between_requests() -> None:
    first = default_request("flip_chip_cbga")
    second = default_request("flip_chip_cbga")
    first.bga.omitted_cells.append({"row": 0, "column": 0})
    assert second.bga.omitted_cells == []


def test_removed_boundary_configuration_is_rejected_and_not_exported() -> None:
    client = TestClient(create_app())
    defaults = client.get("/api/templates/bare_die/defaults").json()
    assert "environment" not in defaults
    generated = client.post("/api/templates/bare_die/generate", json=defaults)
    assert generated.status_code == 200
    assert generated.json()["boundaries"] == []
    defaults["environment"] = {"ambient_temperature_k": 300}
    assert client.post("/api/templates/bare_die/generate", json=defaults).status_code == 422


def test_default_loader_rejects_paths_outside_the_library() -> None:
    with pytest.raises(ValueError, match="within the library"):
        library.read_defaults("../pyproject.toml", "packstudio.template-defaults/v1")


def test_changing_default_selection_does_not_relabel_it_as_captured(isolated_library: Path) -> None:
    def update(payload):
        next(item for item in payload["fields"] if item["control"] == "footprint")["default"] = (
            "CBGAFC_100_9X9mm"
        )

    edit_json(isolated_library / "templates/flip_chip_cbga.json", update)
    model = generate(default_request("flip_chip_cbga"))
    assert model.metadata["preset_geometry_status"] == "source-adapted"
    substrate = next(block for block in model.blocks if block.name == "Package substrate")
    assert substrate.size.x == substrate.size.y == 9


def test_missing_source_adapter_fails_without_legacy_fallback(isolated_library: Path) -> None:
    edit_json(
        isolated_library / "source_adapters.json", lambda data: data["families"].pop("cbga_fc")
    )
    with pytest.raises(ValueError, match="missing source adapter"):
        generate(default_request("flip_chip_cbga"))


def test_transcription_is_portable_across_windows_and_git_line_endings(tmp_path: Path) -> None:
    transcribe = runpy.run_path(str(ROOT / "tools/transcribe_default_parameters.py"))["transcribe"]
    record = {
        "path": "flocentral/flopack/example/example.des",
        "family": "example",
        "sha256": "original-vendor-hash",
        "fields": {"D": "6", "notes": "first\r\nsecond"},
    }
    payload = json.dumps({"records": [record]}, indent=2)
    manifests = []
    for index, line_ending in enumerate(["\n", "\r\n"]):
        snapshot = tmp_path / f"source-{index}.json"
        snapshot.write_text(payload, encoding="utf-8", newline=line_ending)
        output = tmp_path / f"output-{index}"
        manifest = transcribe(snapshot, output)
        serialized = output / "flotherm/example.json"
        assert b"\r\n" not in serialized.read_bytes()
        assert (
            hashlib.sha256(serialized.read_bytes()).hexdigest() == manifest["families"][0]["sha256"]
        )
        data = json.loads(serialized.read_text(encoding="utf-8"))["records"][0]
        assert data["raw_fields"] == record["fields"]
        assert data["source_sha256"] == "original-vendor-hash"
        manifests.append(manifest)
    assert manifests[0] == manifests[1]
