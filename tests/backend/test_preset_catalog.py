"""Catalog integrity, native evidence and offline material reference checks."""

import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from packstudio.catalog_storage import read_catalog_entry
from packstudio.default_parameters import library_directory
from packstudio.material_catalog import MaterialCatalog
from packstudio.preset_catalog import PresetCatalog
from tools.pack_catalog_builder import material_names

ROOT = Path(__file__).resolve().parents[2]


def walk_properties(branch: dict):
    for group in branch["groups"].values():
        yield from group["properties"].items()
        for child in group.get("children", {}).values():
            yield from child["properties"].items()


def test_all_presets_are_individual_complete_offline_documents():
    catalog = PresetCatalog()
    ids = catalog.list_ids()
    assert len(ids) == 342
    counts = Counter()
    branches = 0
    for preset_id in ids:
        record = catalog.read(preset_id)
        counts[record["family"]] += 1
        assert record["default_branch"] == "default"
        assert set(record["material_references"]) == material_names(record["branches"])
        original = json.loads((library_directory() / "flotherm" / f"{record['family']}.json")
                              .read_text(encoding="utf-8"))
        source = next(p for p in original["records"] if p["id"] == preset_id)
        assert record["source"]["des_fields"] == source["raw_fields"]
        assert record["source"]["sha256"] == source["source_sha256"]
        expected = {"default", "four_layer"} if record["family"] in {
            "chip_array", "pbga_wb",
        } else {"default"}
        assert set(record["branches"]) == expected
        for branch in record["branches"].values():
            branches += 1
            for name, prop in walk_properties(branch):
                assert prop["comment"], (preset_id, name)
                assert prop["status"] in {
                    "specified", "calculated", "fixed", "user_input", "not_applicable",
                    "not_specified", "action",
                }
                if prop["status"] in {"specified", "calculated", "fixed"}:
                    assert "value" in prop and prop["value"] is not None, (preset_id, name)
            for group in branch["groups"].values():
                for row in group.get("metal_layers", []):
                    if row["status"] == "specified":
                        assert all(row[k] is not None for k in (
                            "depth_m", "thickness_m", "coverage_percent",
                            "z_from_substrate_bottom_m",
                        ))
    assert branches == 416
    assert counts == {"chip_array": 38, "cbga_fc": 49, "pbga_fc": 45, "pqfp": 61,
                      "QFN": 46, "tsop_conv": 67, "pbga_wb": 36}


def test_all_materials_are_named_classified_and_resolvable():
    catalog = MaterialCatalog()
    names = catalog.list_names()
    assert len(names) == len(set(names)) == 131
    categories = set()
    kinds = set()
    for name in names:
        material = catalog.read(name)
        categories.add(material["category"])
        kinds.add(material["conductivity"]["model"])
        assert material["density"]["value"] > 0
        assert material["specific_heat"]["value"] > 0
        assert material["native_storage"]["name"] == name
    assert len(categories) == 10
    assert kinds == {"constant_isotropic", "temperature_dependent", "orthotropic"}
    for preset_id in PresetCatalog().list_ids():
        for name in PresetCatalog().read(preset_id)["material_references"]:
            assert catalog.read(name)["name"] == name


def test_substrate_defaults_and_four_layer_positions_are_not_project_fallbacks():
    catalog = PresetCatalog()
    fc = catalog.read_branch("PBGAFC_49_6X6mm")["groups"]
    assert fc["packageSubstrate"]["properties"]["substrateThicknessA2"]["value"] == 1.15
    wb = catalog.read_branch("PBGA_352_35X35mm")["groups"]
    assert wb["packageSubstrate"]["properties"]["substrateThicknessA2"]["value"] == 0.56
    four = catalog.read_branch("PBGA_121_15X15mm", "four_layer")["groups"]
    assert four["thermalVias"]["properties"]["numberOfThermalViasInXNVx"]["value"] == 3
    layers = [r for r in four["metalLayers"]["metal_layers"] if r["status"] == "specified"]
    assert len(layers) == 4
    assert layers[0]["depth_m"] == 0
    assert layers[1]["depth_m"] == pytest.approx(0.00016866666666666666)
    assert layers[2]["depth_m"] == pytest.approx(0.0003193333333333333)
    assert layers[3]["depth_m"] == pytest.approx(0.000542)
    assert layers[2]["disconnect_to_vias"] is True


def test_cover_children_built_up_tables_and_implicit_die_material_are_preserved():
    branch = PresetCatalog().read_branch("PBGAFC_49_6X6mm", resolve_materials=True)
    cover = branch["groups"]["topCover"]
    assert set(cover["children"]) == {"encapsulant", "lid", "plate"}
    assert cover["properties"]["topCover"]["value"] == "bareDie"
    assert cover["children"]["lid"]["properties"]["lidThicknessTc"]["value"] == 1
    assert len(branch["groups"]["upperBuiltUpRegion"]["metal_layers"]) == 10
    assert branch["groups"]["die"]["properties"]["dieMaterial"]["value"] == "Silicon (Pure)"
    assert branch["materials"]["Silicon (Pure)"]["conductivity"]["model"] == "temperature_dependent"


def test_native_masks_counts_and_getter_fallback_have_explicit_semantics():
    chip = PresetCatalog().read_branch("ChipArray_48_6X6mm_0_5")["groups"]
    depop = chip["solderBallDepopulation"]["properties"]
    cells = depop["depopulationDialog"]["value"]["native_cell_list"]
    assert len(cells) == 48
    assert {"column": 0, "row": 0} not in cells
    # Native realised wire count uses the 7x7 array when the depopulation switch is off.
    assert chip["bondWires"]["properties"]["numberOfBondWiresNw"]["value"] == 49
    qfn = PresetCatalog().read_branch("QFN_10X10_44")["groups"]
    assert qfn["modelingOptions"]["properties"]["numberOfDiscreteBondwireSteps"]["value"] == 1
    sop = PresetCatalog().read_branch("TSSOP_10_3x3")
    assert sop["wizard"]["sopPackageType"]["value"] == "tssop"


def test_readers_isolate_mutations_and_reject_invalid_names_paths_and_hashes():
    catalog = PresetCatalog()
    original = catalog.read("PBGAFC_49_6X6mm")
    original["branches"].clear()
    assert catalog.read("PBGAFC_49_6X6mm")["branches"]
    material = MaterialCatalog().read("Copper (Pure)")
    material["density"]["value"] = 0
    assert MaterialCatalog().read("Copper (Pure)")["density"]["value"] == 8930
    for operation in (lambda: catalog.read("../request"),
                      lambda: catalog.read_branch("PBGAFC_49_6X6mm", "four_layer"),
                      lambda: MaterialCatalog().read("missing"),
                      lambda: read_catalog_entry("../README.md", "schema", "0" * 64),
                      lambda: read_catalog_entry("presets/index.json", "schema", "0" * 64)):
        with pytest.raises(ValueError):
            operation()


def test_all_json_files_match_index_and_have_utf8_lf_stable_bytes():
    for category, section in (("presets", "presets"), ("materials", "materials")):
        root = library_directory() / category
        index = json.loads((root / "index.json").read_text(encoding="utf-8"))
        files = {p.relative_to(root).as_posix() for p in root.glob("*/*.json")}
        assert files == {r["file"] for r in index[section].values()}
        for entry in index[section].values():
            data = (root / entry["file"]).read_bytes()
            assert b"\r" not in data and data.endswith(b"\n")
            assert hashlib.sha256(data).hexdigest() == entry["sha256"]
            assert ': null' not in data.decode("utf-8")
