from functools import lru_cache

from packstudio.default_parameters import read_defaults
from packstudio.domain.materials import ConductivityTensor, Material


def make_material(
    identifier: str,
    name: str,
    conductivity: float | tuple[float, float, float],
    density: float,
    specific_heat: float,
    color: str,
) -> Material:
    tensor = (
        ConductivityTensor.isotropic(conductivity)
        if isinstance(conductivity, int | float)
        else ConductivityTensor(x=conductivity[0], y=conductivity[1], z=conductivity[2])
    )
    return Material(
        id=identifier,
        name=name,
        conductivity=tensor,
        density=density,
        specific_heat=specific_heat,
        color=color,
        source="PackStudio built-in transcription of reviewed FloTHERM PACK data",
    )


@lru_cache(maxsize=1)
def production_materials() -> dict[str, Material]:
    payload = read_defaults("materials.json", "packstudio.material-defaults/v1")
    materials = [Material.model_validate(item) for item in payload["materials"]]
    return {material.id: material for material in materials}


def material(identifier: str) -> Material:
    try:
        return production_materials()[identifier]
    except KeyError as error:
        raise ValueError(f"unknown built-in material {identifier}") from error
