from functools import lru_cache

from packstudio.domain.materials import ConductivityTensor, Material


def _material(
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
        source="PackStudio built-in material calibrated from reference data",
    )


@lru_cache(maxsize=1)
def production_materials() -> dict[str, Material]:
    materials = [
        _material("static-air", "Static air", 0.0261, 1.225, 1005, "#DDEAF2"),
        _material("silicon", "Silicon (Pure)", 117.5, 2330, 700, "#667085"),
        _material("alumina", "Alumina (Typical)", 16, 3970, 765, "#C7CED8"),
        _material("bt", "BT substrate", 0.2, 1900, 921, "#2E7D62"),
        _material("pbga-substrate", "PBGA substrate", (20, 20, 4), 1900, 921, "#327A68"),
        _material("epoxy-mold", "Epoxy Overmold (Typical)", 0.68, 1820, 882, "#343B46"),
        _material("eme-7730lf", "EME-7730LF", 0.88, 2010, 882, "#414A57"),
        _material("die-attach", "Die attach adhesive", 2.5, 1800, 900, "#C89042"),
        _material("high-k-die-attach", "High-k die attach", 20, 2500, 700, "#D79A3B"),
        _material("solder-sn63", "Solder (Sn63/Pb37)", 50.9, 8400, 150, "#AEB7C4"),
        _material("solder-pb90", "Solder (Pb90/Sn10)", 36, 10750, 142, "#9EA8B5"),
        _material("underfill", "Flip-Chip Underfill (Typical)", 0.6, 1700, 1000, "#9B6B43"),
        _material("copper", "Copper", 385, 8930, 385, "#C46A32"),
        _material("leadframe-c194", "Cu-C19400", 260, 8800, 385, "#B96331"),
        _material("gold", "Gold bond wire", 317, 19300, 129, "#D9A928"),
        _material("solder-mask", "Solder Mask Material", 0.25, 1200, 1000, "#216C4A"),
        _material("tim", "Thermal interface material", 3, 2500, 900, "#B9A78D"),
        _material("lid-copper", "Copper lid", 385, 8930, 385, "#A8572B"),
    ]
    return {material.id: material for material in materials}


def material(identifier: str) -> Material:
    try:
        return production_materials()[identifier]
    except KeyError as error:
        raise ValueError(f"unknown built-in material {identifier}") from error
