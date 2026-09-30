import hashlib

import pytest

from packstudio.default_parameters import library_directory, read_defaults
from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.catalog import generate, schema
from packstudio.templates.package_library.core.parameters import BgaConfiguration, TemplateRequest
from packstudio.templates.package_library.core.source_ball_pattern import source_bga_pattern


def request(template_id: str, preset: str, **parameters) -> TemplateRequest:
    return TemplateRequest(
        template_id=template_id, overrides={f"{template_id}.footprint.size": preset}, **parameters
    )


def test_removal_counts_are_derived_from_fully_populated_rows() -> None:
    model = generate(request("wirebond_pbga", "PBGA_352_35X35mm"))
    assert model.metadata["solder_ball_count"] == 352  # 26² - (26 - 8)²
    footprint = schema("wirebond_pbga")["steps"][0]["fields"][0]
    pattern = footprint["preset_bga"]["PBGA_352_35X35mm"]
    assert pattern["removal_rows"] == pattern["removal_columns"] == 18


def test_explicit_pattern_settings_override_source_defaults() -> None:
    model = generate(
        request(
            "wirebond_pbga", "PBGA_352_35X35mm", bga=BgaConfiguration(solder_removal_enabled=False)
        )
    )
    assert model.metadata["solder_ball_count"] == 26 * 26


def test_partial_bga_request_retains_source_pattern() -> None:
    model = generate(
        request(
            "wirebond_pbga", "PBGA_352_35X35mm", bga=BgaConfiguration(representation="discrete")
        )
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


@pytest.mark.parametrize("preset,count", [("PBGA_576_40X40mm", 576), ("PBGA_845_40X40mm", 845)])
def test_parity_mismatches_are_explicitly_audited(preset: str, count: int) -> None:
    model = generate(request("wirebond_pbga", preset))
    assert model.metadata["solder_ball_count"] == count
    assert "半个节距" in model.metadata["preset_notes"]
    assert model.metadata["preset_geometry_status"] == "source-adapted"


def test_filename_count_does_not_invent_omitted_cells() -> None:
    model = generate(request("flip_chip_cbga", "CBGAFC_416_23X23mm"))
    assert model.metadata["solder_ball_count"] == 420
    assert "416" in model.metadata["preset_notes"]
    assert "420" in model.metadata["preset_notes"]


def test_source_presets_leave_branch_and_power_controls_independent() -> None:
    footprint = schema("flip_chip_cbga")["steps"][0]["fields"][0]
    assert all(
        "flip_chip_cbga.cover.type" not in values and "flip_chip_cbga.die.power" not in values
        for values in footprint["preset_values"].values()
    )


def test_persisted_export_audit_covers_all_sources_and_current_inputs() -> None:
    report = read_defaults("adaptation_report.json", "packstudio.source-adaptation-audit/v1")
    assert report["source_count"] == len(report["records"]) == 342
    assert report["model_export_cases"] == 510
    assert len({record["preset_source_path"] for record in report["records"]}) == 342
    for relative, digest in report["input_sha256"].items():
        assert hashlib.sha256((library_directory() / relative).read_bytes()).hexdigest() == digest
    assert all(
        case["ecxml_xsd"] == case["pta_xml"] == "passed"
        for record in report["records"]
        for case in record["cases"].values()
    )


@pytest.mark.parametrize(
    "preset,count",
    [
        ("ChipArray_48_6X6mm_0_5", 48),
        ("ChipArray_80_9X9mm_0_8", 80),
    ],
)
def test_source_ball_coordinates_remove_only_the_declared_corner(preset: str, count: int) -> None:
    model = generate(request("fbga_fsbga", preset))
    assert model.metadata["solder_ball_count"] == count
    assert "逐球坐标" in model.metadata["preset_notes"]
    footprint = schema("fbga_fsbga")["steps"][0]["fields"][0]
    pattern = footprint["preset_bga"][preset]
    assert pattern["removal_rows"] == pattern["removal_columns"] == 0
    assert pattern["omitted_cells"] == [{"row": 0, "column": 0}]


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
            "fbga_fsbga",
            "ChipArray_48_6X6mm_0_5",
            bga=BgaConfiguration(solder_removal_enabled=False),
        )
    )
    assert model.metadata["solder_ball_count"] == 49


def test_explicit_only_removal_requires_both_dimensions_zero() -> None:
    with pytest.raises(ValueError, match="both region dimensions"):
        generate(
            request(
                "flip_chip_cbga",
                "CBGAFC_49_6X6mm",
                bga=BgaConfiguration(
                    solder_removal_enabled=True,
                    removal_rows=0,
                    removal_columns=1,
                ),
            )
        )
