from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from packstudio.templates.package_library.parameters import TemplateRequest, TemplateValue

type TemplateBuilder = Callable[["TemplateValues", TemplateRequest], Any]


@dataclass(frozen=True)
class FieldDefinition:
    key: str
    step: str
    label: str
    control: str
    default: TemplateValue
    unit: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    options: tuple[TemplateValue, ...] = ()
    visible_when: dict[str, TemplateValue] = field(default_factory=dict)
    enabled_when: dict[str, TemplateValue] = field(default_factory=dict)

    def target_id(self, template_id: str) -> str:
        return f"{template_id}.{self.key}"


@dataclass(frozen=True)
class TemplateDefinition:
    id: str
    display_name: str
    category: str
    fields: tuple[FieldDefinition, ...]
    builder: TemplateBuilder
    has_bga: bool = False
    has_flip_chip: bool = False

    def schema(self) -> dict[str, Any]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in self.fields:
            supported = list(item.options)
            if not supported and item.minimum is not None and item.maximum is not None:
                supported = [item.minimum, item.maximum]
            grouped.setdefault(item.step, []).append(
                {
                    "target_id": item.target_id(self.id),
                    "ui_location": item.step,
                    "component": item.step,
                    "label": item.label,
                    "control": item.control,
                    "default": item.default,
                    "unit": item.unit,
                    "options": list(item.options),
                    "classification": _classification(item),
                    "property_name": item.key,
                    "supported_values": supported,
                    "evidence_status": "implemented",
                    "editable": True,
                    "visible_when": item.visible_when or None,
                    "enabled_when": item.enabled_when or None,
                }
            )
        return {
            "schema_version": "packstudio.wizard/v2",
            "template_id": self.id,
            "steps": [
                {"id": step, "label": _step_label(step), "fields": items}
                for step, items in grouped.items()
            ],
            "has_bga": self.has_bga,
            "special_rules": {
                "bga_pattern": ("implicit_full_with_center_and_removal" if self.has_bga else None),
                "flip_chip_bumps": ("thick_orthotropic_equivalent" if self.has_flip_chip else None),
            },
        }

    def validate_request(self, request: TemplateRequest) -> "TemplateValues":
        if request.template_id != self.id:
            raise ValueError(f"request template_id must be {self.id}")
        if request.bga is not None and not self.has_bga:
            raise ValueError("BGA configuration is only valid for BGA templates")
        by_target = {item.target_id(self.id): item for item in self.fields}
        unknown = sorted(set(request.overrides) - set(by_target))
        if unknown:
            raise ValueError(f"unknown production template parameters: {unknown}")
        values = {item.key: item.default for item in self.fields}
        for target_id, value in request.overrides.items():
            item = by_target[target_id]
            _validate_value(item, value)
            values[item.key] = value
        inactive = [
            item.target_id(self.id)
            for item in self.fields
            if item.target_id(self.id) in request.overrides
            and (not _matches(item.visible_when, values) or not _matches(item.enabled_when, values))
        ]
        if inactive:
            raise ValueError(f"parameters are inactive in the current branch: {inactive}")
        return TemplateValues(values)


class TemplateValues:
    def __init__(self, values: dict[str, TemplateValue]) -> None:
        self._values = values

    def number(self, key: str) -> float:
        value = self._values[key]
        if not isinstance(value, int | float) or isinstance(value, bool):
            raise ValueError(f"{key} is not numeric")
        return float(value)

    def integer(self, key: str) -> int:
        value = self.number(key)
        if not value.is_integer():
            raise ValueError(f"{key} must be an integer")
        return int(value)

    def boolean(self, key: str) -> bool:
        value = self._values[key]
        if not isinstance(value, bool):
            raise ValueError(f"{key} is not boolean")
        return value

    def text(self, key: str) -> str:
        value = self._values[key]
        if not isinstance(value, str):
            raise ValueError(f"{key} is not text")
        return value


def _validate_value(item: FieldDefinition, value: TemplateValue) -> None:
    if item.control == "checkbox" and not isinstance(value, bool):
        raise ValueError(f"{item.key} must be boolean")
    if item.control in {"number", "integer", "integer_spinbox"}:
        if not isinstance(value, int | float) or isinstance(value, bool):
            raise ValueError(f"{item.key} must be numeric")
        numeric = float(value)
        if item.control.startswith("integer") and not numeric.is_integer():
            raise ValueError(f"{item.key} must be an integer")
        if item.minimum is not None and numeric < item.minimum:
            raise ValueError(f"{item.key} must be at least {item.minimum}")
        if item.maximum is not None and numeric > item.maximum:
            raise ValueError(f"{item.key} must be at most {item.maximum}")
    if item.options and value not in item.options:
        raise ValueError(f"{item.key} must be one of {list(item.options)}")


def _matches(conditions: dict[str, TemplateValue], values: dict[str, TemplateValue]) -> bool:
    return all(values.get(key) == expected for key, expected in conditions.items())


def _classification(item: FieldDefinition) -> str:
    if item.control == "checkbox":
        return "boolean_option"
    if item.control in {"number", "integer", "integer_spinbox"}:
        return "numeric_parameter"
    return "enum_option"


def _step_label(identifier: str) -> str:
    labels = {
        "package": "封装",
        "die": "芯片",
        "substrate": "基板",
        "encapsulant": "塑封",
        "interconnect": "互连",
        "leadframe": "引线框",
        "bond_wires": "键合线",
        "options": "建模选项",
    }
    return labels.get(identifier, identifier.replace("_", " ").title())
