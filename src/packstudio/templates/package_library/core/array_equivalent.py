from dataclasses import dataclass
from math import pi, sqrt

from packstudio.domain.materials import ConductivityTensor, Material


@dataclass(frozen=True)
class EquivalentLayerProperties:
    conductivity: ConductivityTensor
    density: float
    specific_heat: float
    fill_fraction: float
    replacement_side: float


def calculate_cylindrical_array_equivalent(
    element: Material,
    matrix: Material,
    radius: float,
    pitch_x: float,
    pitch_y: float,
) -> EquivalentLayerProperties:
    """Apply the section-4 equal-volume square-column resistance network."""
    if min(radius, pitch_x, pitch_y) <= 0:
        raise ValueError("radius and pitches must be positive")
    if 2 * radius > min(pitch_x, pitch_y):
        raise ValueError("cylindrical elements overlap at the requested pitch")

    replacement_side = sqrt(pi) * radius
    if replacement_side >= min(pitch_x, pitch_y):
        raise ValueError("equal-volume square does not fit inside the unit cell")

    fill_fraction = pi * radius**2 / (pitch_x * pitch_y)
    conductivity_x = _in_plane_conductivity(
        direction_pitch=pitch_x,
        transverse_pitch=pitch_y,
        replacement_side=replacement_side,
        element_k=element.conductivity.x,
        matrix_k=matrix.conductivity.x,
    )
    conductivity_y = _in_plane_conductivity(
        direction_pitch=pitch_y,
        transverse_pitch=pitch_x,
        replacement_side=replacement_side,
        element_k=element.conductivity.y,
        matrix_k=matrix.conductivity.y,
    )
    conductivity_z = (
        fill_fraction * element.conductivity.z + (1 - fill_fraction) * matrix.conductivity.z
    )
    density = fill_fraction * element.density + (1 - fill_fraction) * matrix.density
    volumetric_heat_capacity = (
        fill_fraction * element.density * element.specific_heat
        + (1 - fill_fraction) * matrix.density * matrix.specific_heat
    )

    return EquivalentLayerProperties(
        conductivity=ConductivityTensor(
            x=conductivity_x,
            y=conductivity_y,
            z=conductivity_z,
        ),
        density=density,
        specific_heat=volumetric_heat_capacity / density,
        fill_fraction=fill_fraction,
        replacement_side=replacement_side,
    )


def create_equivalent_material(
    material_id: str,
    name: str,
    element: Material,
    matrix: Material,
    radius: float,
    pitch_x: float,
    pitch_y: float,
) -> tuple[Material, EquivalentLayerProperties]:
    properties = calculate_cylindrical_array_equivalent(
        element=element,
        matrix=matrix,
        radius=radius,
        pitch_x=pitch_x,
        pitch_y=pitch_y,
    )
    material = Material(
        id=material_id,
        name=name,
        conductivity=properties.conductivity,
        density=properties.density,
        specific_heat=properties.specific_heat,
        color=element.color,
        source="Section 4 cylindrical bump + matrix anisotropic equivalence; "
        f"element={element.id}; matrix={matrix.id};",
    )
    return material, properties


def _in_plane_conductivity(
    direction_pitch: float,
    transverse_pitch: float,
    replacement_side: float,
    element_k: float,
    matrix_k: float,
) -> float:
    series_term = (direction_pitch - replacement_side) / (matrix_k * direction_pitch)
    parallel_denominator = matrix_k * (transverse_pitch - replacement_side) + (
        element_k * replacement_side
    )
    central_term = (replacement_side * transverse_pitch) / (direction_pitch * parallel_denominator)
    return 1 / (series_term + central_term)
