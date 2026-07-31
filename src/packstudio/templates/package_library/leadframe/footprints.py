from packstudio.templates.package_library.core.definitions import PresetOption
from packstudio.templates.package_library.core.fields import footprint


def qfn_footprint_field():
    return footprint(
        "QFN_12X12_100",
        (
            _qfn("QFN_12X12_100", 12, 100, 0.4, 0.2, 0.5, 5.4, 10.8, 2.75),
            _qfn("QFN_6X6_36", 6, 36, 0.5, 0.25, 0.4, 2.7, 4.8, 1.2),
            _qfn("QFN_3X3_8", 3, 8, 0.65, 0.3, 0.55, 1.35, 1.8, 0.225),
        ),
    )


def qfp_footprint_field():
    return footprint(
        "LQFP_32_7X7mm",
        (
            _qfp(
                "LQFP_32_7X7mm",
                32,
                body_length=7,
                body_width=7,
                die_length=2.1,
                die_width=2.1,
                flag_length=2.94,
                flag_width=2.94,
                count_x=8,
                count_y=8,
                pitch=0.8,
                lead_width=0.4,
                gap_x=0.42,
                gap_y=0.42,
            ),
            _qfp(
                "LQFP_100_14X20mm",
                100,
                body_length=20,
                body_width=14,
                die_length=6,
                die_width=4.2,
                flag_length=8,
                flag_width=5.88,
                count_x=30,
                count_y=20,
                pitch=0.65,
                lead_width=0.3,
                gap_x=1,
                gap_y=0.84,
            ),
            _qfp(
                "LQFP_208_28X28mm",
                208,
                body_length=28,
                body_width=28,
                die_length=8.4,
                die_width=8.4,
                flag_length=10.4,
                flag_width=10.4,
                count_x=52,
                count_y=52,
                pitch=0.5,
                lead_width=0.2,
                gap_x=1,
                gap_y=1,
            ),
        ),
    )


def soic_footprint_field():
    return footprint(
        "SOP_8_3_81x4_93",
        (
            _soic(
                "SOP_8_3_81x4_93",
                8,
                body_length=4.93,
                body_width=3.81,
                overall_width=6,
                standoff=0.15,
                body_thickness=1.47,
                die_length=1.479,
                die_width=1.143,
                flag_length=1.7748,
                flag_width=1.3716,
                gap=0.114,
                lead_height=0.635,
                foot_length=0.5475,
            ),
            _soic(
                "SOP_28_7_6x17_9",
                28,
                body_length=17.93,
                body_width=7.62,
                overall_width=10.31,
                standoff=0.23,
                body_thickness=2.34,
                die_length=5.379,
                die_width=2.286,
                flag_length=6.379,
                flag_width=2.7432,
                gap=0.228,
                lead_height=1.07,
                foot_length=0.6725,
            ),
            _soic(
                "SOP_44_13_3x28_2",
                44,
                body_length=28.19,
                body_width=13.33,
                overall_width=16,
                standoff=0.23,
                body_thickness=2.31,
                die_length=8.457,
                die_width=3.999,
                flag_length=9.457,
                flag_width=4.7988,
                gap=0.398,
                lead_height=1.055,
                foot_length=0.6675,
            ),
        ),
    )


def _qfn(
    value: str,
    size: float,
    leads: int,
    pitch: float,
    lead_width: float,
    lead_length: float,
    die: float,
    pad: float,
    wire_length: float,
) -> PresetOption:
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
            "leads.width": lead_width,
            "leads.length": lead_length,
            "bond_wire.length_x": wire_length,
            "bond_wire.length_y": wire_length,
        },
    )


def _qfp(
    value: str,
    pins: int,
    *,
    body_length: float,
    body_width: float,
    die_length: float,
    die_width: float,
    flag_length: float,
    flag_width: float,
    count_x: int,
    count_y: int,
    pitch: float,
    lead_width: float,
    gap_x: float,
    gap_y: float,
) -> PresetOption:
    return PresetOption(
        value=value,
        label=f"LQFP · {pins} 引脚 · {body_width:g} × {body_length:g} mm 本体",
        values={
            "package.length": body_length + 2,
            "package.width": body_width + 2,
            "body.length": body_length,
            "body.width": body_width,
            "die.length": die_length,
            "die.width": die_width,
            "flag.length": flag_length,
            "flag.width": flag_width,
            "leads.count_x": count_x,
            "leads.count_y": count_y,
            "leads.pitch": pitch,
            "leads.width": lead_width,
            "leads.gap_x": gap_x,
            "leads.gap_y": gap_y,
            "bond_wire.count": pins,
        },
    )


def _soic(
    value: str,
    pins: int,
    *,
    body_length: float,
    body_width: float,
    overall_width: float,
    standoff: float,
    body_thickness: float,
    die_length: float,
    die_width: float,
    flag_length: float,
    flag_width: float,
    gap: float,
    lead_height: float,
    foot_length: float,
) -> PresetOption:
    return PresetOption(
        value=value,
        label=f"SOP · {pins} 引脚 · {body_width:g} × {body_length:g} mm 本体",
        values={
            "package.length": body_length,
            "package.width": overall_width,
            "package.standoff": standoff,
            "body.length": body_length,
            "body.width": body_width,
            "body.thickness": body_thickness,
            "die.length": die_length,
            "die.width": die_width,
            "flag.length": flag_length,
            "flag.width": flag_width,
            "leads.total": pins,
            "leads.gap": gap,
            "leads.pitch": 1.27,
            "leads.width": 0.4,
            "leads.thickness": 0.2,
            "leads.height": lead_height,
            "leads.foot_length": foot_length,
            "bond_wire.count": pins,
        },
    )
