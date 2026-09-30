from collections.abc import Callable
from dataclasses import dataclass, field
from math import isfinite
from typing import Any

from packstudio.templates.package_library.core.parameters import (
    BgaConfiguration,
    TemplateRequest,
    TemplateValue,
)
from packstudio.templates.package_library.core.step_labels import step_label

type TemplateBuilder = Callable[["TemplateValues", TemplateRequest], Any]


@dataclass(frozen=True)
class PresetOption:
    value: str
    label: str
    values: dict[str, TemplateValue]
    bga: BgaConfiguration | None = None
    metadata: dict[str, str] = field(default_factory=dict)


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
    option_labels: dict[str, str] = field(default_factory=dict)
    presets: tuple[PresetOption, ...] = ()
    visible_when: dict[str, TemplateValue] = field(default_factory=dict)
    enabled_when: dict[str, TemplateValue] = field(default_factory=dict)

    def target_id(self, template_id: str) -> str:
        return f"{template_id}.{self.key}"


@dataclass(frozen=True)
class MaterialSelectionDefinition:
    group_id: str
    step: str
    label: str
    default: str
    options: tuple[str, ...]
    visible_when: dict[str, TemplateValue] = field(default_factory=dict)

    def target_id(self, template_id: str) -> str:
        return f"{template_id}.material.{self.group_id.removeprefix('group-')}"


@dataclass(frozen=True)
class TemplateDefinition:
    id: str
    display_name: str
    category: str
    fields: tuple[FieldDefinition, ...]
    builder: TemplateBuilder
    step_order: tuple[str, ...] = ()
    material_selections: tuple[MaterialSelectionDefinition, ...] = ()
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
                    "minimum": item.minimum,
                    "maximum": item.maximum,
                    "options": list(item.options),
                    "option_labels": item.option_labels or None,
                    "preset_values": (
                        {
                            preset.value: {
                                f"{self.id}.{key}": value for key, value in preset.values.items()
                            }
                            for preset in item.presets
                        }
                        or None
                    ),
                    "classification": _classification(item),
                    "preset_bga": {
                        p.value: p.bga.model_dump(mode="json")
                        for p in item.presets
                        if p.bga is not None
                    }
                    or None,
                    "preset_notes": {
                        p.value: p.metadata["preset_notes"]
                        for p in item.presets
                        if p.metadata.get("preset_notes")
                    }
                    or None,
                    "property_name": item.key,
                    "supported_values": supported,
                    "evidence_status": "implemented",
                    "editable": True,
                    "material_group_id": None,
                    "visible_when": item.visible_when or None,
                    "enabled_when": item.enabled_when or None,
                }
            )
        for item in self.material_selections:
            grouped.setdefault(item.step, []).append(
                {
                    "target_id": item.target_id(self.id),
                    "ui_location": item.step,
                    "component": item.group_id,
                    "label": item.label,
                    "control": "material",
                    "default": item.default,
                    "unit": None,
                    "minimum": None,
                    "maximum": None,
                    "options": list(item.options),
                    "classification": "material_option",
                    "property_name": f"material.{item.group_id}",
                    "supported_values": list(item.options),
                    "evidence_status": "implemented",
                    "editable": True,
                    "material_group_id": item.group_id,
                    "visible_when": item.visible_when or None,
                    "enabled_when": None,
                }
            )
        ordered_steps = [
            *[step for step in self.step_order if step in grouped],
            *[step for step in grouped if step not in self.step_order],
        ]
        return {
            "schema_version": "packstudio.wizard/v2",
            "template_id": self.id,
            "steps": [
                {"id": step, "label": step_label(step), "fields": items}
                for step in ordered_steps
                for items in (grouped[step],)
            ],
            "has_bga": self.has_bga,
            "special_rules": {
                "outline_type": "standard_outline",
                "die_type": "actual_type",
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
        by_key = {item.key: item for item in self.fields}
        unknown = sorted(set(request.overrides) - set(by_target))
        if unknown:
            raise ValueError(f"unknown production template parameters: {unknown}")
        values = {item.key: item.default for item in self.fields}
        for item in self.fields:
            if not item.presets:
                continue
            selected = request.overrides.get(item.target_id(self.id), item.default)
            preset = next(
                (candidate for candidate in item.presets if candidate.value == selected),
                None,
            )
            if preset is None:
                raise ValueError(f"{item.key} has no preset named {selected}")
            unknown_targets = sorted(set(preset.values) - {field.key for field in self.fields})
            if unknown_targets:
                raise ValueError(f"{item.key} preset targets unknown fields: {unknown_targets}")
            for key, value in preset.values.items():
                _validate_value(by_key[key], value)
            values.update(preset.values)
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
        self._validate_material_assignments(request, values)
        return TemplateValues(values)

    def _validate_material_assignments(
        self,
        request: TemplateRequest,
        values: dict[str, TemplateValue],
    ) -> None:
        selections = {item.group_id: item for item in self.material_selections}
        unknown = sorted(set(request.material_assignments) - set(selections))
        if unknown:
            raise ValueError(f"unknown component material groups: {unknown}")
        invalid = [
            f"{group_id}={material_id}"
            for group_id, material_id in request.material_assignments.items()
            if material_id not in selections[group_id].options
        ]
        if invalid:
            raise ValueError(f"materials are not allowed for these components: {invalid}")
        inactive = [
            group_id
            for group_id in request.material_assignments
            if not _matches(selections[group_id].visible_when, values)
        ]
        if inactive:
            raise ValueError(f"material assignments are inactive: {inactive}")


class TemplateValues:
    def __init__(self, values: dict[str, TemplateValue]) -> None:
        self._values = values

    def matches(self, conditions: dict[str, TemplateValue]) -> bool:
        return _matches(conditions, self._values)

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
        if not isfinite(numeric):
            raise ValueError(f"{item.key} must be finite")
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
    if item.control == "footprint":
        return "jedec_preset"
    if item.control == "checkbox":
        return "boolean_option"
    if item.control in {"number", "integer", "integer_spinbox"}:
        return "numeric_parameter"
    return "enum_option"
