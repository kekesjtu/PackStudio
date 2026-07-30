from functools import lru_cache

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
    materials = [
        make_material("static-air", "Static air", 0.0261, 1.1614, 1007, "#DDEAF2"),
        make_material("silicon", "Silicon (Pure)", 117.5, 2330, 700, "#667085"),
        make_material("alumina", "Alumina (Typical)", 16, 3970, 765, "#C7CED8"),
        make_material("bt", "BT", 0.2, 1900, 921, "#2E7D62"),
        make_material(
            "pbga-substrate",
            "Substrate PBGAFC (Typical)",
            (20, 20, 4),
            1900,
            921,
            "#327A68",
        ),
        make_material(
            "epoxy-mold",
            "Epoxy Overmold (Typical)",
            0.68,
            1820,
            882,
            "#343B46",
        ),
        make_material("eme-7730lf", "EME-7730LF", 0.88, 2010, 1, "#414A57"),
        make_material(
            "dieattach-84-1lmis",
            "DieAttach-84-1LMIS",
            2.5,
            1,
            1,
            "#C89042",
        ),
        make_material("qmi-595", "QMI 595", 1.4, 1, 1, "#C89042"),
        make_material("ablestik-8510aa", "Ablestik 8510AA", 2, 1, 1, "#C89042"),
        make_material(
            "dieattach-2600bt",
            "DieAttach-2600BT",
            20,
            1,
            1,
            "#D79A3B",
        ),
        make_material("die-attach", "DieAttach-84-1LMIS", 2.5, 1, 1, "#C89042"),
        make_material(
            "high-k-die-attach",
            "DieAttach-2600BT",
            20,
            1,
            1,
            "#D79A3B",
        ),
        make_material(
            "solder-sn63",
            "Solder (Sn63/Pb37)",
            50.9,
            8400,
            150,
            "#AEB7C4",
        ),
        make_material("solder-pb90", "Solder (Pb90/Sn10)", 36, 10750, 142, "#9EA8B5"),
        make_material(
            "underfill",
            "Flip-Chip Underfill (Typical)",
            0.6,
            1,
            1,
            "#9B6B43",
        ),
        make_material("copper", "Copper (Pure)", 385, 8930, 385, "#C46A32"),
        make_material("leadframe-c194", "Cu-C19400", 260, 8800, 1, "#B96331"),
        make_material("gold", "Gold (Pure)", 317, 19300, 129, "#D9A928"),
        make_material("solder-mask", "Solder Mask Material", 0.25, 1, 1, "#216C4A"),
        make_material("tim", "Thermal interface material", 3, 2500, 900, "#B9A78D"),
        make_material("lid-copper", "Copper lid", 385, 8930, 385, "#A8572B"),
        make_material("aluminum", "Aluminum (Pure)", 201, 2710, 913, "#A8B0BA"),
        make_material(
            "flip-cap-grease",
            "Flip-Chip Cap Grease (Typical)",
            3.3,
            1,
            1,
            "#C9BDAA",
        ),
        make_material(
            "stiffener-adhesive",
            "Stiffener Adhesive (Typical)",
            0.8,
            1,
            1,
            "#9A7556",
        ),
    ]
    return {material.id: material for material in materials}


def material(identifier: str) -> Material:
    try:
        return production_materials()[identifier]
    except KeyError as error:
        raise ValueError(f"unknown built-in material {identifier}") from error
