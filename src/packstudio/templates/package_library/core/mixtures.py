"""Constituent volume fractions with mass-weighted specific heat."""

from packstudio.domain.materials import ConductivityTensor, Material


def mix_material(
    original: Material,
    metal: Material,
    matrix: Material,
    fraction: float,
    parallel_axes: set[str],
    *,
    include_matrix_conductivity: bool = True,
) -> Material:
    if not 0 <= fraction <= 1:
        raise ValueError(f"{original.id} metal volume fraction must be within [0, 1]")
    density = fraction * metal.density + (1 - fraction) * matrix.density
    specific_heat = (
        fraction * metal.density * metal.specific_heat
        + (1 - fraction) * matrix.density * matrix.specific_heat
    ) / density
    conductivity = {}
    for axis in "xyz":
        matrix_k = getattr(matrix.conductivity, axis)
        conductivity[axis] = (
            fraction * getattr(metal.conductivity, axis)
            + ((1 - fraction) * matrix_k if include_matrix_conductivity else 0)
            if axis in parallel_axes
            else matrix_k
        )
    return original.model_copy(
        update={
            "conductivity": ConductivityTensor(**conductivity),
            "density": density,
            "specific_heat": specific_heat,
            "source": f"PACK derived mixture; metal={metal.id}; matrix={matrix.id}; "
            f"volume_fraction={fraction:.16g}",
        }
    )
