from packstudio.templates.package_library.core.definitions import PresetOption
from packstudio.templates.package_library.core.fields import footprint


def bare_die_footprint_field():
    return footprint(
        "DIE_4_9X4_9X0_22",
        tuple(
            PresetOption(
                value=value,
                label=f"裸芯片 · {length:g} × {width:g} × {thickness:g} mm",
                values={
                    "die.length": length,
                    "die.width": width,
                    "die.thickness": thickness,
                },
            )
            for value, length, width, thickness in (
                ("DIE_4_9X4_9X0_22", 4.9, 4.9, 0.22),
                ("DIE_3X3X0_2", 3, 3, 0.2),
                ("DIE_5X5X0_3", 5, 5, 0.3),
                ("DIE_10X10X0_5", 10, 10, 0.5),
            )
        ),
        label="芯片尺寸预设",
    )
