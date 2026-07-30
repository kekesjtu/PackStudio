from packstudio.templates.package_library.core.definitions import FieldDefinition
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
) -> FieldDefinition:
    return FieldDefinition(
        key=key,
        step=step,
        label=label,
        control="select",
        default=default,
        options=options,
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
