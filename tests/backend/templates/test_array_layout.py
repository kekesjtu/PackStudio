import pytest
from pydantic import ValidationError

from packstudio.templates.flip_chip_cbga.layout import (
    build_array_cells,
    occupied_regions,
    unoccupied_regions,
)
from packstudio.templates.flip_chip_cbga.material_library import default_materials
from packstudio.templates.flip_chip_cbga.parameters import (
    ArrayLayerParameters,
    ArrayPattern,
    CellIndex,
)


def test_full_array_has_one_uniform_region() -> None:
    parameters = _parameters(rows=7, columns=7)

    cells = build_array_cells(parameters)

    assert sum(cell.present for cell in cells) == 49
    assert len(occupied_regions(parameters)) == 1
    assert unoccupied_regions(parameters) == []


def test_staggered_rows_shift_by_half_a_pitch() -> None:
    parameters = _parameters(rows=3, columns=3, pattern=ArrayPattern.STAGGERED)

    cells = build_array_cells(parameters)
    first_row_x = [cell.center_x for cell in cells if cell.row == 0]
    second_row_x = [cell.center_x for cell in cells if cell.row == 1]

    assert second_row_x[0] - first_row_x[0] == pytest.approx(parameters.pitch_x / 2)
    assert len(occupied_regions(parameters)) == 3


def test_center_depopulation_splits_outer_ring_into_four_regions() -> None:
    parameters = _parameters(
        rows=7,
        columns=7,
        pattern=ArrayPattern.CENTER_DEPOPULATED,
        center_rows=3,
        center_columns=3,
    )

    cells = build_array_cells(parameters)

    assert sum(cell.present for cell in cells) == 40
    assert len(occupied_regions(parameters)) == 4
    assert len(unoccupied_regions(parameters)) == 1


def test_center_population_keeps_center_as_a_distinct_region() -> None:
    parameters = _parameters(
        rows=7,
        columns=7,
        pattern=ArrayPattern.CENTER_POPULATED,
        center_rows=3,
        center_columns=3,
    )

    cells = build_array_cells(parameters)
    groups = {
        group: sum(cell.present and cell.group == group for cell in cells)
        for group in {
            "perimeter",
            "center",
        }
    }

    assert groups == {"perimeter": 40, "center": 9}
    assert len(occupied_regions(parameters)) == 5


def test_custom_center_omission_is_partitioned_without_partial_regions() -> None:
    omitted = [CellIndex(row=row, column=column) for row in (1, 2) for column in (1, 2)]
    parameters = _parameters(
        rows=4,
        columns=4,
        pattern=ArrayPattern.CUSTOM,
        omitted_cells=omitted,
    )

    assert sum(cell.present for cell in build_array_cells(parameters)) == 12
    assert len(occupied_regions(parameters)) == 4
    assert len(unoccupied_regions(parameters)) == 1


def test_asymmetric_center_region_is_rejected() -> None:
    with pytest.raises(ValidationError, match="symmetric"):
        _parameters(
            rows=7,
            columns=7,
            pattern=ArrayPattern.CENTER_DEPOPULATED,
            center_rows=2,
            center_columns=3,
        )


def test_custom_pattern_cannot_remove_every_element() -> None:
    omitted = [CellIndex(row=row, column=column) for row in range(2) for column in range(2)]

    with pytest.raises(ValidationError, match="retain at least one"):
        _parameters(
            rows=2,
            columns=2,
            pattern=ArrayPattern.CUSTOM,
            omitted_cells=omitted,
        )


def _parameters(**overrides: object) -> ArrayLayerParameters:
    materials = default_materials()
    values: dict[str, object] = {
        "rows": 3,
        "columns": 3,
        "pitch_x": 0.5,
        "pitch_y": 0.5,
        "diameter": 0.2,
        "height": 0.1,
        "element_material": materials["solder"],
        "matrix_material": materials["underfill"],
    }
    values.update(overrides)
    return ArrayLayerParameters.model_validate(values)
