from packstudio.templates.package_library.core.definitions import PresetOption
from packstudio.templates.package_library.core.fields import footprint


def wirebond_pbga_footprint_field():
    return footprint(
        "PBGA_121_15X15mm",
        (
            _pbga(
                "PBGA_121_15X15mm",
                121,
                package=15,
                substrate=0.36,
                encapsulant=13,
                encapsulant_thickness=0.8,
                die=4.5,
                flag=6.5,
                wire_extent=8.5,
                array_side=11,
                ball_diameter=0.75,
                ball_height=0.6,
            ),
            _pbga(
                "PBGA_352_35X35mm",
                352,
                package=35,
                substrate=0.56,
                encapsulant=30,
                encapsulant_thickness=1.17,
                die=10.5,
                flag=12.5,
                wire_extent=14.5,
                array_side=26,
                ball_diameter=0.75,
                ball_height=0.6,
            ),
            _pbga(
                "PBGA_896_40X40mm",
                896,
                package=40,
                substrate=0.56,
                encapsulant=38.7,
                encapsulant_thickness=1.17,
                die=12,
                flag=14,
                wire_extent=16,
                array_side=31,
                ball_diameter=0.5,
                ball_height=0.5,
            ),
        ),
    )


def fbga_footprint_field():
    return footprint(
        "ChipArray_24_4X4mm_0_8",
        (
            _fbga(
                "ChipArray_24_4X4mm_0_8",
                24,
                length=4,
                width=4,
                die=1.2,
                wire_extent=2,
                array_side=5,
                pitch=0.8,
                via_offset=0.4,
            ),
            _fbga(
                "ChipArray_100_10X10mm_0_8",
                100,
                length=10,
                width=10.67,
                die=3,
                wire_extent=8,
                array_side=10,
                pitch=0.8,
                via_offset=0.4,
            ),
            _fbga(
                "ChipArray_324_19X19mm_1",
                324,
                length=19,
                width=19,
                die=5.7,
                wire_extent=17,
                array_side=18,
                pitch=1.0,
                via_offset=0.5,
            ),
        ),
    )


def _pbga(
    value: str,
    nominal_balls: int,
    *,
    package: float,
    substrate: float,
    encapsulant: float,
    encapsulant_thickness: float,
    die: float,
    flag: float,
    wire_extent: float,
    array_side: int,
    ball_diameter: float,
    ball_height: float,
) -> PresetOption:
    return PresetOption(
        value=value,
        label=f"PBGA_{nominal_balls} · {package:g} × {package:g} mm",
        values={
            "package.length": package,
            "package.width": package,
            "substrate.thickness": substrate,
            "encapsulant.length": encapsulant,
            "encapsulant.width": encapsulant,
            "encapsulant.thickness": encapsulant_thickness,
            "die.length": die,
            "die.width": die,
            "flag.length": flag,
            "flag.width": flag,
            "bond_wire.total": nominal_balls,
            "bond_wire.extent_length": wire_extent,
            "bond_wire.extent_width": wire_extent,
            "bga.columns": array_side,
            "bga.rows": array_side,
            "bga.pitch": 1.27,
            "bga.diameter": ball_diameter,
            "bga.height": ball_height,
        },
    )


def _fbga(
    value: str,
    nominal_balls: int,
    *,
    length: float,
    width: float,
    die: float,
    wire_extent: float,
    array_side: int,
    pitch: float,
    via_offset: float,
) -> PresetOption:
    return PresetOption(
        value=value,
        label=(f"ChipArray_{nominal_balls} · {length:g} × {width:g} mm · {pitch:g} mm 间距"),
        values={
            "package.length": length,
            "package.width": width,
            "die.length": die,
            "die.width": die,
            "bond_wire.extent_length": wire_extent,
            "bond_wire.extent_width": wire_extent,
            "vias.offset_x": via_offset,
            "vias.offset_y": via_offset,
            "bga.columns": array_side,
            "bga.rows": array_side,
            "bga.pitch": pitch,
            "bga.diameter": 0.46,
            "bga.height": 0.4,
        },
    )
