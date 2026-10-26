from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path

from packstudio.domain.materials import ConductivityTensor, Material
from packstudio.material_catalog import MaterialCatalog
from packstudio.runtime_data import read_defaults


@lru_cache(maxsize=1)
def production_materials() -> dict[str, Material]:
    payload = read_defaults("materials/runtime.json", "packstudio.runtime-materials/v1")
    catalog = MaterialCatalog()
    index = read_defaults("materials/index.json", "packstudio.material-index/v1")["materials"]
    definitions = {
        Path(entry["file"]).stem: {"name": name, "color": "#aeb7bf"}
        for name, entry in index.items()
    }
    definitions.update(payload["aliases"])
    materials = {item["id"]: Material.model_validate(item) for item in payload["project_materials"]}
    for identifier, entry in definitions.items():
        record = catalog.read(entry["name"])
        conductivity = record["conductivity"]
        tensor = (
            ConductivityTensor(**{axis: conductivity[axis] for axis in "xyz"})
            if conductivity["model"] == "orthotropic"
            else ConductivityTensor.isotropic(conductivity["value"])
        )
        materials[identifier] = Material(
            id=identifier,
            name=record["name"],
            conductivity=tensor,
            density=record["density"]["value"],
            specific_heat=record["specific_heat"]["value"],
            color=entry["color"],
            source="PACK built-in material; "
            + (
                "constant conductivity at native reference temperature "
                f"{conductivity['reference_temperature']} C; temperature law retained in catalog"
                if conductivity["model"] == "temperature_dependent"
                else conductivity["model"]
            ),
        )
    return materials


def material_id_for_name(name: str) -> str:
    matches = [item.id for item in production_materials().values() if item.name == name]
    if not matches:
        raise ValueError(f"unknown PACK material name: {name}")
    # Existing short physical-material IDs keep builder and component references readable.
    return min(matches, key=lambda identifier: (len(identifier), identifier))


def material(identifier: str, custom_materials: Sequence[Material] = ()) -> Material:
    for item in reversed(custom_materials):
        if item.id == identifier:
            return item
    try:
        return production_materials()[identifier]
    except KeyError as error:
        raise ValueError(f"unknown built-in material {identifier}") from error
