from packstudio.templates.package_library.core.definitions import (
    MaterialSelectionDefinition,
)
from packstudio.templates.package_library.core.parameters import TemplateValue


def selection(
    group_id: str,
    step: str,
    label: str,
    default: str,
    options: tuple[str, ...],
    *,
    visible_when: dict[str, TemplateValue] | None = None,
) -> MaterialSelectionDefinition:
    if default not in options:
        raise ValueError(f"default material {default} must be one of {options}")
    return MaterialSelectionDefinition(
        group_id=group_id,
        step=step,
        label=label,
        default=default,
        options=options,
        visible_when=visible_when or {},
    )


DIE = selection("group-die", "die", "芯片材料", "silicon", ("silicon",))
ENCAPSULANT = selection(
    "group-encapsulant",
    "encapsulant",
    "塑封材料",
    "epoxy-mold",
    ("epoxy-mold", "eme-7730lf"),
)
FLIP_ENCAPSULANT = selection(
    "group-encapsulant",
    "encapsulant",
    "塑封材料",
    "epoxy-mold",
    ("epoxy-mold", "eme-7730lf"),
    visible_when={"cover.type": "encapsulant"},
)
DIE_ATTACH = selection(
    "group-die-attach",
    "die",
    "芯片粘接材料",
    "die-attach",
    ("die-attach", "high-k-die-attach"),
)
HIGH_K_DIE_ATTACH = selection(
    "group-die-attach",
    "die",
    "芯片粘接材料",
    "high-k-die-attach",
    ("high-k-die-attach", "die-attach"),
)
LEAD_FRAME = selection(
    "group-lead-frame",
    "leadframe",
    "引线框材料",
    "leadframe-c194",
    ("leadframe-c194", "copper"),
)
BOND_WIRES = selection(
    "group-bond-wires",
    "bond_wires",
    "键合线材料",
    "gold",
    ("gold",),
)
