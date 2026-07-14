import pytest
from pydantic import ValidationError

from packstudio.templates.flip_chip_cbga.layout import (
    build_array_cells,
    occupied_regions,
    unoccupied_regions,
)
from packstudio.templates.flip_chip_cbga.material_library import default_materials
from packstudio.templates.flip_chip_cbga.parameters import CellIndex, SolderBallParameters


def test_full_array_has_one_uniform_region() -> None:
    parameters = _parameters(rows=7, columns=7)

    cells = build_array_cells(parameters)

    assert sum(cell.present for cell in cells) == 49
    assert len(occupied_regions(parameters)) == 1
    assert unoccupied_regions(parameters) == []


def test_center_removal_splits_outer_ring_into_four_regions() -> None:
    parameters = _parameters(
        rows=7,
        columns=7,
        solder_removal_enabled=True,
        removal_rows=3,
        removal_columns=3,
    )

    cells = build_array_cells(parameters)

    assert sum(cell.present for cell in cells) == 40
    assert len(occupied_regions(parameters)) == 4
    assert len(unoccupied_regions(parameters)) == 1


def test_center_solder_keeps_center_as_a_distinct_region() -> None:
    parameters = _parameters(
        rows=7,
        columns=7,
        center_solder_enabled=True,
        center_solder_rows=3,
        center_solder_columns=3,
    )

    cells = build_array_cells(parameters)
    groups = {
        group: sum(cell.present and cell.group == group for cell in cells)
        for group in {"perimeter", "center"}
    }

    assert groups == {"perimeter": 40, "center": 9}
    assert len(occupied_regions(parameters)) == 5


def test_center_solder_can_be_restored_inside_a_larger_removed_region() -> None:
    parameters = _parameters(
        rows=7,
        columns=7,
        solder_removal_enabled=True,
        removal_rows=5,
        removal_columns=5,
        center_solder_enabled=True,
        center_solder_rows=3,
        center_solder_columns=3,
    )

    cells = build_array_cells(parameters)
    groups = {
        group: sum(cell.present and cell.group == group for cell in cells)
        for group in {"perimeter", "center"}
    }

    assert groups == {"perimeter": 24, "center": 9}
    assert sum(not cell.present for cell in cells) == 16
    assert len(unoccupied_regions(parameters)) == 4


def test_explicit_removal_takes_priority_over_center_solder() -> None:
    parameters = _parameters(
        rows=5,
        columns=5,
        solder_removal_enabled=True,
        removal_rows=3,
        removal_columns=3,
        center_solder_enabled=True,
        center_solder_rows=1,
        center_solder_columns=1,
        omitted_cells=[CellIndex(row=2, column=2)],
    )

    center = next(cell for cell in build_array_cells(parameters) if cell.row == cell.column == 2)

    assert center.present is False
    assert center.group == "void"


def test_asymmetric_center_region_is_rejected() -> None:
    with pytest.raises(ValidationError, match="symmetric"):
        _parameters(
            rows=7,
            columns=7,
            solder_removal_enabled=True,
            removal_rows=2,
            removal_columns=3,
        )


def test_center_solder_must_fit_inside_removal_region() -> None:
    with pytest.raises(ValidationError, match="fit inside"):
        _parameters(
            rows=7,
            columns=7,
            solder_removal_enabled=True,
            removal_rows=3,
            removal_columns=3,
            center_solder_enabled=True,
            center_solder_rows=5,
            center_solder_columns=5,
        )


def test_solder_style_cannot_remove_every_element() -> None:
    outer_cells = [
        CellIndex(row=row, column=column)
        for row in range(3)
        for column in range(3)
        if (row, column) != (1, 1)
    ]

    with pytest.raises(ValidationError, match="retain at least one"):
        _parameters(
            rows=3,
            columns=3,
            solder_removal_enabled=True,
            removal_rows=1,
            removal_columns=1,
            omitted_cells=outer_cells,
        )


def test_removed_pattern_field_is_rejected() -> None:
    with pytest.raises(ValidationError, match="pattern"):
        _parameters(pattern="staggered")


def _parameters(**overrides: object) -> SolderBallParameters:
    materials = default_materials()
    values: dict[str, object] = {
        "rows": 3,
        "columns": 3,
        "pitch_x": 0.5,
        "pitch_y": 0.5,
        "diameter": 0.2,
        "height": 0.1,
        "center_solder_rows": 1,
        "center_solder_columns": 1,
        "removal_rows": 1,
        "removal_columns": 1,
        "element_material": materials["solder"],
        "matrix_material": materials["air"],
    }
    values.update(overrides)
    return SolderBallParameters.model_validate(values)
