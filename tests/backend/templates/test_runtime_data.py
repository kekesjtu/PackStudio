import hashlib
import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import packstudio.runtime_data as library
from packstudio.api.app import create_app
from packstudio.templates.package_library.catalog import (
    default_request,
    definitions,
    generate,
    schema,
)
from packstudio.templates.package_library.core.materials import production_materials
from tools.pack_reference.des import source_record


@pytest.mark.parametrize("layout", ["source", "wheel", "frozen"])
def test_runtime_data_is_loaded_from_the_active_installation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, layout: str
) -> None:
    checkout = tmp_path / "checkout"
    prefix = tmp_path / "installed"
    extracted = tmp_path / "extracted"
    monkeypatch.setattr(library, "__file__", str(checkout / "src/packstudio/runtime_data.py"))
    original_get_path = library.sysconfig.get_path
    monkeypatch.setattr(
        library.sysconfig,
        "get_path",
        lambda key: str(prefix) if key == "data" else original_get_path(key),
    )
    monkeypatch.setattr(library.sys, "frozen", layout == "frozen", raising=False)
    monkeypatch.setattr(library.sys, "_MEIPASS", str(extracted), raising=False)
    directory = {"source": checkout, "wheel": prefix, "frozen": extracted}[layout] / "runtime_data"
    directory.mkdir(parents=True)
    (directory / "pack_bindings.json").write_text(
        json.dumps(
            {"schema_version": "packstudio.pack-bindings/v1", "families": {"sample": 2}}
        ),
        encoding="utf-8",
    )
    library._read.cache_clear()
    try:
        assert library.library_directory() == directory
        assert library.read_default_value(
            "pack_bindings.json", "packstudio.pack-bindings/v1", "families", "sample"
        ) == 2
    finally:
        library._read.cache_clear()


@pytest.fixture
def isolated_library(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    copied = tmp_path / "runtime_data"
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


def edit_indexed(directory: Path, category: str, key: str, update) -> None:
    index_path = directory / category / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    entry = index[category][key]
    path = directory / category / entry["file"]
    edit_json(path, update)
    entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    index_path.write_text(json.dumps(index), encoding="utf-8")


def test_json_changes_drive_geometry_and_schema(isolated_library: Path) -> None:
    def update(payload):
        payload["branches"]["default"]["groups"]["die"]["properties"]["dieThicknessTd"]["value"] = (
            0.28
        )

    edit_indexed(isolated_library, "presets", "CBGAFC_49_6X6mm", update)
    model = generate(default_request("cbga_fc"))
    die = next(block for block in model.blocks if block.name == "Silicon die")
    assert die.size.z == pytest.approx(0.28)
    fields = [item for step in schema("cbga_fc")["steps"] for item in step["fields"]]
    assert (
        next(item for item in fields if item["property_name"] == "die.thickness")["default"] == 0.28
    )


def test_source_preset_values_are_read_at_runtime(isolated_library: Path) -> None:
    def update(payload):
        payload["branches"]["default"]["groups"]["die"]["properties"]["dieLengthLd"]["value"] = 1.9

    edit_indexed(isolated_library, "presets", "CBGAFC_49_6X6mm", update)
    model = generate(default_request("cbga_fc"))
    die = next(block for block in model.blocks if block.name == "Silicon die")
    assert die.size.x == 1.9


def test_material_defaults_come_from_json(isolated_library: Path) -> None:
    edit_indexed(
        isolated_library,
        "materials",
        "Silicon (Pure)",
        lambda payload: payload["conductivity"].update(value=123),
    )
    model = generate(default_request("bare_die"))
    assert model.materials[0].conductivity.x == 123


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
            footprint = next(item for item in payload["fields"] if item["control"] == "footprint")
            footprint["presets"][0]["values"]["die.thickness"] = float("nan")

        edit_json(path, update)
    with pytest.raises(ValueError):
        generate(default_request("bare_die"))


def test_request_defaults_are_not_shared_between_requests() -> None:
    first = default_request("cbga_fc")
    second = default_request("cbga_fc")
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


def test_selected_defaults_keep_nested_mutations_out_of_the_cache() -> None:
    arguments = ("presets/index.json", "packstudio.preset-index/v1", "presets")
    identifiers = library.read_default_keys(*arguments)
    assert len(identifiers) == 342
    original = library.read_default_value(*arguments, identifiers[0])
    changed = library.read_default_value(*arguments, identifiers[0])
    changed.clear()
    assert library.read_default_value(*arguments, identifiers[0]) == original
    template_arguments = ("templates/cbga_fc.json", "packstudio.template-defaults/v1", "fields")
    fields = library.read_default_value(*template_arguments)
    fields.clear()
    assert library.read_default_value(*template_arguments)


def test_changing_default_selection_does_not_relabel_it_as_captured(isolated_library: Path) -> None:
    def update(payload):
        next(item for item in payload["fields"] if item["control"] == "footprint")["default"] = (
            "CBGAFC_100_9X9mm"
        )

    edit_json(isolated_library / "templates/cbga_fc.json", update)
    model = generate(default_request("cbga_fc"))
    assert model.metadata["preset_geometry_status"] == "native-defaults-adapted"
    substrate = next(block for block in model.blocks if block.name == "Package substrate")
    assert substrate.size.x == substrate.size.y == 9


def test_missing_source_adapter_fails_without_legacy_fallback(isolated_library: Path) -> None:
    edit_json(isolated_library / "pack_bindings.json", lambda data: data["families"].pop("cbga_fc"))
    with pytest.raises(ValueError, match="missing native PACK binding"):
        generate(default_request("cbga_fc"))


def test_original_des_parser_preserves_blanks_and_rejects_duplicates(tmp_path: Path) -> None:
    path = tmp_path / "example.des"
    path.write_text("D|6\nempty|\nmaterial|Copper (Pure)\n", encoding="utf-8")
    record = source_record(path, tmp_path)
    assert record["raw_fields"] == {"D": "6", "empty": "", "material": "Copper (Pure)"}
    assert record["source_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    path.write_text("D|6\nD|7\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        source_record(path, tmp_path)


@pytest.mark.parametrize("section", ["center", "removal"])
def test_native_blank_bga_counts_require_input_only_after_enabling(section: str) -> None:
    client = TestClient(create_app())
    payload = client.get("/api/templates/cbga_fc/defaults").json()
    prefix = "center_solder" if section == "center" else "removal"
    switch = "center_solder_enabled" if section == "center" else "solder_removal_enabled"
    assert payload["bga"][f"{prefix}_rows"] is None
    assert payload["bga"][f"{prefix}_columns"] is None
    assert client.post("/api/templates/cbga_fc/generate", json=payload).status_code == 200
    payload["bga"][switch] = True
    missing = client.post("/api/templates/cbga_fc/generate", json=payload)
    assert missing.status_code == 422
    assert "requires both row and column counts" in missing.json()["detail"]
    payload["bga"].update({f"{prefix}_rows": 1, f"{prefix}_columns": 1})
    assert client.post("/api/templates/cbga_fc/generate", json=payload).status_code == 200
    payload["bga"][f"{prefix}_rows"] = None
    assert client.post("/api/templates/cbga_fc/export/floxml", json=payload).status_code == 422


def test_disabled_native_branch_keeps_values_when_the_source_supplies_them(
    isolated_library: Path,
) -> None:
    def update(payload):
        fields = payload["branches"]["default"]["groups"]["centralBalls"]["properties"]
        fields["numberCentralRowsMDp"].update(value=3, status="specified")
        fields["numberCentralRowsMEp"].update(value=3, status="specified")

    edit_indexed(isolated_library, "presets", "CBGAFC_49_6X6mm", update)
    client = TestClient(create_app())
    payload = client.get("/api/templates/cbga_fc/defaults").json()
    assert payload["bga"]["center_solder_enabled"] is False
    assert payload["bga"]["center_solder_rows"] == payload["bga"]["center_solder_columns"] == 3
    assert generate(default_request("cbga_fc")).metadata["solder_ball_count"] == 49


def test_missing_native_via_dimensions_stay_blank_after_enabling() -> None:
    client = TestClient(create_app())
    result = client.get("/api/templates/qfn/schema").json()
    fields = {f["property_name"]: f for step in result["steps"] for f in step["fields"]}
    for key in ("vias.length", "vias.diameter", "vias.plating", "vias.pitch", "vias.rows"):
        assert fields[key]["default"] is None
    payload = client.get("/api/templates/qfn/defaults").json()
    assert payload["vias"]["removal_rows"] is None
    payload["overrides"]["qfn.vias.enabled"] = True
    response = client.post("/api/templates/qfn/generate", json=payload)
    assert response.status_code == 422
    assert "vias.diameter requires a value" in response.json()["detail"]
