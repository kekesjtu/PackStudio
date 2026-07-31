from packstudio.templates.package_library.core.definitions import PresetOption
from packstudio.templates.package_library.core.fields import footprint


def wirebond_pbga_footprint_field():
    return footprint(
        "PBGA_121_15X15mm",
        tuple(
            _pbga(value, balls, size, side, pitch)
            for value, balls, size, side, pitch in (
                ("PBGA_121_15X15mm", 121, 15, 11, 1.27),
                ("PBGA_169_23X23mm", 169, 23, 13, 1.27),
                ("PBGA_196_15X15mm", 196, 15, 14, 1.0),
                ("PBGA_256_17X17mm", 256, 17, 16, 1.0),
                ("PBGA_324_23X23mm", 324, 23, 18, 1.27),
            )
        ),
    )


def fbga_footprint_field():
    return footprint(
        "ChipArray_24_4X4mm_0_8",
        tuple(
            _fbga(value, balls, size, side, pitch)
            for value, balls, size, side, pitch in (
                ("ChipArray_24_4X4mm_0_8", 24, 4, 5, 0.8),
                ("ChipArray_49_7X7mm_0_8", 49, 7, 7, 0.8),
                ("ChipArray_64_8X8mm_0_8", 64, 8, 8, 0.8),
                ("ChipArray_81_10X10mm_1", 81, 10, 9, 1.0),
                ("ChipArray_100_10X10mm_0_8", 100, 10, 10, 0.8),
            )
        ),
    )


def _pbga(value: str, balls: int, size: float, side: int, pitch: float) -> PresetOption:
    return PresetOption(
        value=value,
        label=f"PBGA · {balls} 球 · {size:g} × {size:g} mm",
        values={
            "package.length": size,
            "package.width": size,
            "encapsulant.length": size - 2,
            "encapsulant.width": size - 2,
            "bond_wire.total": balls,
            "bga.columns": side,
            "bga.rows": side,
            "bga.pitch": pitch,
        },
    )


def _fbga(value: str, balls: int, size: float, side: int, pitch: float) -> PresetOption:
    return PresetOption(
        value=value,
        label=f"芯片阵列 · {balls} 球 · {size:g} × {size:g} mm · {pitch:g} mm 间距",
        values={
            "package.length": size,
            "package.width": size,
            "bga.columns": side,
            "bga.rows": side,
            "bga.pitch": pitch,
        },
    )
