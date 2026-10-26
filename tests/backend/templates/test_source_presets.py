import hashlib
import json
from pathlib import Path

import pytest

from packstudio.domain.enums import StructureType
from packstudio.runtime_data import library_directory
from packstudio.templates.package_library.catalog import generate, schema
from packstudio.templates.package_library.core.parameters import BgaConfiguration, TemplateRequest
from packstudio.templates.package_library.core.source_ball_pattern import source_bga_pattern


def request(template_id: str, preset: str, **parameters) -> TemplateRequest:
    return TemplateRequest(
        template_id=template_id, overrides={f"{template_id}.footprint.size": preset}, **parameters
    )


def test_removal_counts_are_derived_from_fully_populated_rows() -> None:
    model = generate(request("pbga_wb", "PBGA_352_35X35mm"))
    assert model.metadata["solder_ball_count"] == 352  # 26² - (26 - 8)²
    footprint = schema("pbga_wb")["steps"][0]["fields"][0]
    pattern = footprint["preset_bga"]["PBGA_352_35X35mm"]
    assert pattern["removal_rows"] == pattern["removal_columns"] == 18


def test_explicit_pattern_settings_override_source_defaults() -> None:
    model = generate(
        request("pbga_wb", "PBGA_352_35X35mm", bga=BgaConfiguration(solder_removal_enabled=False))
    )
    assert model.metadata["solder_ball_count"] == 26 * 26


def test_partial_bga_request_retains_source_pattern() -> None:
    model = generate(
        request("pbga_wb", "PBGA_352_35X35mm", bga=BgaConfiguration(representation="discrete"))
    )
    assert model.metadata["solder_ball_count"] == 352
    assert model.metadata["solder_ball_representation"] == "discrete"


def test_two_sided_qfn_omits_absent_leads_and_wires() -> None:
    model = generate(request("qfn", "QFN_3X3_6"))
    assert model.metadata["lead_count"] == 6
    wires = [block for block in model.blocks if block.structure_type is StructureType.BOND_WIRE]
    assert wires
    assert all("left" not in block.id and "right" not in block.id for block in wires)
    assert "two-sided" in model.metadata["preset_notes"]


def test_qfn_rejects_removing_all_leads() -> None:
    with pytest.raises(ValueError, match="at least one"):
        generate(
            TemplateRequest(
                template_id="qfn",
                overrides={
                    "qfn.leads.count_x": 0,
                    "qfn.leads.count_y": 0,
                },
            )
        )


def test_clearing_a_populated_qfn_side_does_not_turn_it_into_an_absent_side() -> None:
    with pytest.raises(ValueError, match="leads.count_y requires a value"):
        generate(TemplateRequest(template_id="qfn", overrides={"qfn.leads.count_y": None}))


@pytest.mark.parametrize("preset,count", [("PBGA_576_40X40mm", 576), ("PBGA_845_40X40mm", 845)])
def test_parity_mismatches_are_explicitly_audited(preset: str, count: int) -> None:
    model = generate(request("pbga_wb", preset))
    assert model.metadata["solder_ball_count"] == count
    assert "半个节距" in model.metadata["preset_notes"]
    assert model.metadata["preset_geometry_status"] == "native-defaults-adapted"


def test_filename_count_does_not_invent_omitted_cells() -> None:
    model = generate(request("cbga_fc", "CBGAFC_416_23X23mm"))
    assert model.metadata["solder_ball_count"] == 420
    assert "416" in model.metadata["preset_notes"]
    assert "420" in model.metadata["preset_notes"]


def test_native_cover_and_power_defaults_are_part_of_preset_values() -> None:
    footprint = schema("cbga_fc")["steps"][0]["fields"][0]
    assert all(
        values["cbga_fc.cover.type"] == "bare_die" and values["cbga_fc.die.power"] == 0
        for values in footprint["preset_values"].values()
    )


def test_persisted_export_audit_covers_all_sources_and_current_inputs() -> None:
    report = json.loads(
        (Path(__file__).parents[3] / "docs/validation/catalog_presets.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["source_count"] == len(report["records"]) == 342
    assert report["schema_version"] == "packstudio.catalog-adaptation-audit/v2"
    assert report["model_export_cases"] == 510
    assert len({record["preset_source_path"] for record in report["records"]}) == 342
    for relative, digest in report["input_sha256"].items():
        assert hashlib.sha256((library_directory() / relative).read_bytes()).hexdigest() == digest
    assert all(
        case["geometry_references"] == case["floxml_xsd"] == "passed"
        and case["floxml_cuboids"] == case["physical_blocks"]
        for record in report["records"]
        for case in record["cases"].values()
    )


@pytest.mark.parametrize(
    "preset,count",
    [
        ("ChipArray_48_6X6mm_0_5", 49),
        ("ChipArray_80_9X9mm_0_8", 81),
    ],
)
def test_inactive_native_ball_coordinates_do_not_enable_removal(preset: str, count: int) -> None:
    model = generate(request("chip_array", preset))
    assert model.metadata["solder_ball_count"] == count
    assert "逐球坐标" in model.metadata["preset_notes"]
    footprint = schema("chip_array")["steps"][0]["fields"][0]
    pattern = footprint["preset_bga"][preset]
    assert pattern["omitted_cells"] == []
    assert pattern["solder_removal_enabled"] is False


def test_source_coordinate_axes_are_columns_then_rows() -> None:
    pattern, _ = source_bga_pattern({"MD": 3, "ME": 2, "balls": "2x1"}, {"bga.rows": 2}, "balls")
    assert {(cell["row"], cell["column"]) for cell in pattern["omitted_cells"]} == {
        (0, 0),
        (0, 1),
        (0, 2),
        (1, 0),
        (1, 1),
    }


@pytest.mark.parametrize("balls", ["0x0:0x0", "2x2", "0x0:invalid"])
def test_invalid_source_coordinates_fail_explicitly(balls: str) -> None:
    with pytest.raises(ValueError):
        source_bga_pattern({"MD": 2, "ME": 2, "balls": balls}, {"bga.rows": 2}, "balls")


def test_switching_off_source_coordinate_removal_restores_full_array() -> None:
    model = generate(
        request(
            "chip_array",
            "ChipArray_48_6X6mm_0_5",
            bga=BgaConfiguration(solder_removal_enabled=False),
        )
    )
    assert model.metadata["solder_ball_count"] == 49


def test_explicit_only_removal_requires_both_dimensions_zero() -> None:
    with pytest.raises(ValueError, match="both region dimensions"):
        generate(
            request(
                "cbga_fc",
                "CBGAFC_49_6X6mm",
                bga=BgaConfiguration(
                    solder_removal_enabled=True,
                    removal_rows=0,
                    removal_columns=1,
                ),
            )
        )
