from packstudio.templates.package_library.core.definitions import PresetOption
from packstudio.templates.package_library.core.fields import footprint


def cbga_footprint_field():
    return footprint(
        "CBGAFC_49_6X6mm",
        _flip_chip_presets("CBGAFC"),
    )


def pbga_footprint_field():
    return footprint(
        "PBGAFC_49_6X6mm",
        _flip_chip_presets("PBGAFC"),
    )


def _flip_chip_presets(prefix: str) -> tuple[PresetOption, ...]:
    return tuple(
        PresetOption(
            value=f"{prefix}_{balls}_{size}X{size}mm",
            label=f"{prefix} · {balls} 球 · {size} × {size} mm",
            values={
                "substrate.length": size,
                "substrate.width": size,
                "bga.columns": side,
                "bga.rows": side,
                "bga.pitch": 0.8,
                "bga.diameter": 0.5,
                "bga.height": 0.4,
            },
        )
        for balls, size, side in (
            (49, 6, 7),
            (64, 7, 8),
            (81, 8, 9),
            (100, 9, 10),
            (144, 10, 12),
        )
    )
