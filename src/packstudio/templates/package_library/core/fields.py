from packstudio.templates.package_library.core.definitions import FieldDefinition, PresetOption
from packstudio.templates.package_library.core.parameters import TemplateValue


def number(
    key: str,
    step: str,
    label: str,
    default: float,
    minimum: float,
    maximum: float,
    unit: str = "mm",
    *,
    visible_when: dict[str, TemplateValue] | None = None,
) -> FieldDefinition:
    return FieldDefinition(
        key=key,
        step=step,
        label=label,
        control="number",
        default=default,
        unit=unit,
        minimum=minimum,
        maximum=maximum,
        visible_when=visible_when or {},
    )


def integer(
    key: str,
    step: str,
    label: str,
    default: int,
    minimum: int,
    maximum: int,
    *,
    visible_when: dict[str, TemplateValue] | None = None,
) -> FieldDefinition:
    return FieldDefinition(
        key=key,
        step=step,
        label=label,
        control="integer_spinbox",
        default=default,
        minimum=minimum,
        maximum=maximum,
        visible_when=visible_when or {},
    )


def choice(
    key: str,
    step: str,
    label: str,
    default: str,
    options: tuple[str, ...],
    *,
    option_labels: dict[str, str] | None = None,
) -> FieldDefinition:
    return FieldDefinition(
        key=key,
        step=step,
        label=label,
        control="select",
        default=default,
        options=options,
        option_labels=option_labels or {},
    )


def footprint(
    default: str,
    presets: tuple[PresetOption, ...],
    *,
    label: str = "Footprint 尺寸（JEDEC）",
) -> FieldDefinition:
    options = tuple(preset.value for preset in presets)
    if default not in options:
        raise ValueError(f"default footprint {default} must be one of {options}")
    return FieldDefinition(
        key="footprint.size",
        step="package_setup",
        label=label,
        control="footprint",
        default=default,
        options=options,
        option_labels={preset.value: preset.label for preset in presets},
        presets=presets,
    )


def toggle(
    key: str,
    step: str,
    label: str,
    default: bool = False,
) -> FieldDefinition:
    return FieldDefinition(
        key=key,
        step=step,
        label=label,
        control="checkbox",
        default=default,
    )
