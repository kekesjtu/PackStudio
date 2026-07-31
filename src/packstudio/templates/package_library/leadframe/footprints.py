from packstudio.templates.package_library.core.definitions import PresetOption
from packstudio.templates.package_library.core.fields import footprint


def qfn_footprint_field():
    return footprint(
        "QFN_12X12_100",
        tuple(
            _qfn(value, size, leads, pitch)
            for value, size, leads, pitch in (
                ("QFN_12X12_100", 12, 100, 0.4),
                ("QFN_10X10_68", 10, 68, 0.5),
                ("QFN_8X8_48", 8, 48, 0.5),
                ("QFN_7X7_32", 7, 32, 0.8),
                ("QFN_5X5_32", 5, 32, 0.5),
                ("QFN_4X4_16_0_65", 4, 16, 0.65),
            )
        ),
    )


def qfp_footprint_field():
    return footprint(
        "LQFP_32_7X7mm",
        tuple(
            _qfp(value, pins, body, pitch)
            for value, pins, body, pitch in (
                ("LQFP_32_7X7mm", 32, 7, 0.8),
                ("LQFP_44_10X10mm", 44, 10, 0.8),
                ("LQFP_48_7X7mm", 48, 7, 0.5),
                ("LQFP_64_10X10mm", 64, 10, 0.5),
                ("LQFP_80_12X12mm", 80, 12, 0.5),
                ("LQFP_100_14X14mm", 100, 14, 0.5),
            )
        ),
    )


def soic_footprint_field():
    return footprint(
        "SOP_8_3_81x4_93",
        (
            _soic("SOP_8_3_81x4_93", 8, 4.93, 3.81, 6, 1.27),
            _soic("SOP_14_3_81x8_69", 14, 8.69, 3.81, 6, 1.27),
            _soic("SOP_16_3_81x9_93", 16, 9.93, 3.81, 6, 1.27),
            _soic("SOP_16_7_6x10_3", 16, 10.3, 7.6, 10.3, 1.27),
            _soic("TSSOP_16_4_4x5", 16, 5, 4.4, 6.4, 0.65),
        ),
    )


def _qfn(value: str, size: float, leads: int, pitch: float) -> PresetOption:
    pad = 0.9 * size
    die = 0.45 * size
    side_count = leads // 4
    return PresetOption(
        value=value,
        label=f"QFN · {leads} 引脚 · {size:g} × {size:g} mm",
        values={
            "package.length": size,
            "package.width": size,
            "die.length": die,
            "die.width": die,
            "pad.length": pad,
            "pad.width": pad,
            "pad.exposed_length": pad - 0.25,
            "pad.exposed_width": pad - 0.25,
            "leads.count_x": side_count,
            "leads.count_y": side_count,
            "leads.pitch_x": pitch,
            "leads.pitch_y": pitch,
            "bond_wire.length_x": (pad - die) / 2 + 0.05,
            "bond_wire.length_y": (pad - die) / 2 + 0.05,
        },
    )


def _qfp(value: str, pins: int, body: float, pitch: float) -> PresetOption:
    return PresetOption(
        value=value,
        label=f"LQFP · {pins} 引脚 · {body:g} × {body:g} mm 本体",
        values={
            "package.length": body + 2,
            "package.width": body + 2,
            "body.length": body,
            "body.width": body,
            "leads.count_x": pins // 4,
            "leads.count_y": pins // 4,
            "leads.pitch": pitch,
            "bond_wire.count": pins,
        },
    )


def _soic(
    value: str,
    pins: int,
    body_length: float,
    body_width: float,
    overall_width: float,
    pitch: float,
) -> PresetOption:
    family = "TSSOP" if value.startswith("TSSOP") else "SOP"
    return PresetOption(
        value=value,
        label=f"{family} · {pins} 引脚 · {body_width:g} × {body_length:g} mm 本体",
        values={
            "package.length": body_length,
            "package.width": overall_width,
            "body.length": body_length,
            "body.width": body_width,
            "leads.total": pins,
            "leads.pitch": pitch,
            "bond_wire.count": pins,
        },
    )
