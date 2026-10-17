from math import pi, sqrt

import pytest

from packstudio.domain.materials import Material
from packstudio.templates.package_library.core.array_equivalent import (
    calculate_cylindrical_array_equivalent,
)


def test_section_4_closed_form_matches_hand_calculation() -> None:
    element = _material("element", conductivity=100, density=8000, specific_heat=200)
    matrix = _material("matrix", conductivity=1, density=1600, specific_heat=1000)
    radius = 0.05
    pitch = 0.5

    result = calculate_cylindrical_array_equivalent(
        element=element,
        matrix=matrix,
        radius=radius,
        pitch_x=pitch,
        pitch_y=pitch,
    )

    fill_fraction = pi * radius**2 / pitch**2
    replacement_side = sqrt(pi) * radius
    expected_in_plane = 1 / (
        (pitch - replacement_side) / (matrix.conductivity.x * pitch)
        + replacement_side
        / (
            matrix.conductivity.x * (pitch - replacement_side)
            + element.conductivity.x * replacement_side
        )
    )
    expected_z = (
        fill_fraction * element.conductivity.z + (1 - fill_fraction) * matrix.conductivity.z
    )

    assert result.replacement_side == pytest.approx(replacement_side)
    assert result.fill_fraction == pytest.approx(fill_fraction)
    assert result.conductivity.x == pytest.approx(expected_in_plane)
    assert result.conductivity.y == pytest.approx(expected_in_plane)
    assert result.conductivity.z == pytest.approx(expected_z)


def test_density_and_specific_heat_preserve_mass_and_heat_capacity() -> None:
    element = _material("element", conductivity=50, density=8000, specific_heat=250)
    matrix = _material("matrix", conductivity=2, density=2000, specific_heat=1000)

    result = calculate_cylindrical_array_equivalent(
        element=element,
        matrix=matrix,
        radius=0.1,
        pitch_x=0.5,
        pitch_y=0.4,
    )

    fraction = pi * 0.1**2 / (0.5 * 0.4)
    expected_density = fraction * 8000 + (1 - fraction) * 2000
    expected_capacity = (fraction * 8000 * 250 + (1 - fraction) * 2000 * 1000) / expected_density
    assert result.density == pytest.approx(expected_density)
    assert result.specific_heat == pytest.approx(expected_capacity)


def test_rectangular_pitch_produces_direction_specific_in_plane_conductivity() -> None:
    element = _material("element", conductivity=100, density=8000, specific_heat=200)
    matrix = _material("matrix", conductivity=1, density=1600, specific_heat=1000)
    radius, pitch_x, pitch_y = 0.05, 0.4, 0.6

    result = calculate_cylindrical_array_equivalent(
        element=element,
        matrix=matrix,
        radius=radius,
        pitch_x=pitch_x,
        pitch_y=pitch_y,
    )

    side = sqrt(pi) * radius
    expected_x = 1 / (
        (pitch_x - side) / pitch_x + side * pitch_y / (pitch_x * ((pitch_y - side) + 100 * side))
    )
    expected_y = 1 / (
        (pitch_y - side) / pitch_y + side * pitch_x / (pitch_y * ((pitch_x - side) + 100 * side))
    )
    assert result.conductivity.x == pytest.approx(expected_x)
    assert result.conductivity.y == pytest.approx(expected_y)
    assert result.conductivity.x != pytest.approx(result.conductivity.y)


def test_equal_constituent_conductivities_remain_equal_in_all_directions() -> None:
    element = _material("element", conductivity=5, density=8000, specific_heat=250)
    matrix = _material("matrix", conductivity=5, density=2000, specific_heat=1000)

    result = calculate_cylindrical_array_equivalent(
        element=element,
        matrix=matrix,
        radius=0.05,
        pitch_x=0.4,
        pitch_y=0.5,
    )

    assert result.conductivity.x == pytest.approx(5)
    assert result.conductivity.y == pytest.approx(5)
    assert result.conductivity.z == pytest.approx(5)


def test_overlapping_cylinders_are_rejected() -> None:
    material = _material("same", conductivity=5, density=2000, specific_heat=1000)

    with pytest.raises(ValueError, match="overlap"):
        calculate_cylindrical_array_equivalent(
            element=material,
            matrix=material,
            radius=0.3,
            pitch_x=0.5,
            pitch_y=0.5,
        )


def _material(
    material_id: str, conductivity: float, density: float, specific_heat: float
) -> Material:
    return Material(
        id=material_id,
        name=material_id,
        conductivity=conductivity,
        density=density,
        specific_heat=specific_heat,
    )
