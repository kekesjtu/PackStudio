from collections.abc import Callable
from dataclasses import dataclass, field
from math import isfinite
from typing import Any

from packstudio.templates.package_library.core.parameters import (
    BgaConfiguration,
    TemplateRequest,
    TemplateValue,
)
from packstudio.templates.package_library.core.wizard_schema import build_wizard_schema

type TemplateBuilder = Callable[["TemplateValues", TemplateRequest], Any]


@dataclass(frozen=True)
class PresetOption:
    value: str
    label: str
    values: dict[str, TemplateValue]
    bga: BgaConfiguration | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    material_assignments: dict[str, str] = field(default_factory=dict)


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
    help_text: str | None = None

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
        return build_wizard_schema(self)

    def resolve_material_request(
        self, request: TemplateRequest, values: "TemplateValues"
    ) -> TemplateRequest:
        footprint = next((f for f in self.fields if f.control == "footprint"), None)
        preset = (
            next(p for p in footprint.presets if p.value == values.text(footprint.key))
            if footprint
            else None
        )
        defaults = {
            item.group_id: (
                preset.material_assignments.get(item.group_id, item.default)
                if preset
                else item.default
            )
            for item in self.material_selections
            if values.matches(item.visible_when)
        }
        return request.model_copy(
            update={"material_assignments": {**defaults, **request.material_assignments}}
        )

    def validate_request(self, request: TemplateRequest) -> "TemplateValues":
        if request.template_id != self.id:
            raise ValueError(f"request template_id must be {self.id}")
        if request.bga is not None and not self.has_bga:
            raise ValueError("BGA configuration is only valid for BGA templates")
        if (
            request.bga is not None
            and request.bga.representation == "isotropic"
            and self.id != "pbga_wb"
        ):
            raise ValueError("Isotropic Cuboid solder balls are only available for Wirebond PBGA")
        if request.vias is not None and not any(f.key == "vias.enabled" for f in self.fields):
            raise ValueError("via configuration is only valid for templates with thermal vias")
        if self.id == "chip_array" and request.vias is not None and request.vias.removal_enabled:
            raise ValueError("Chip Array 通孔去除由焊球主阵列控制")
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
        from packstudio.templates.package_library.core.family_initialization import (
            initialize_family_values,
        )

        initialize_family_values(self.id, values, request.overrides)
        for target_id, value in request.overrides.items():
            item = by_target[target_id]
            _validate_value(item, value)
            values[item.key] = value
        if "package.type" in by_key:
            footprint = next(item for item in self.fields if item.control == "footprint")
            preset = next(p for p in footprint.presets if p.value == values[footprint.key])
            if values["package.type"] != preset.values["package.type"]:
                raise ValueError("Package Type does not match the selected footprint")
        inactive = [
            item.target_id(self.id)
            for item in self.fields
            if item.target_id(self.id) in request.overrides
            and (not _matches(item.visible_when, values) or not _matches(item.enabled_when, values))
        ]
        if inactive:
            raise ValueError(f"parameters are inactive in the current branch: {inactive}")
        optional = {
            "metal.hole_length",
            "metal.hole_width",
            "upper.count",
            "lower.count",
            "upper.plating",
            "lower.plating",
        }
        for target_id, value in request.overrides.items():
            if value is None and by_target[target_id].key not in optional:
                raise ValueError(f"{by_target[target_id].key} requires a value")
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

    def is_missing(self, key: str) -> bool:
        return self._values[key] is None

    def number(self, key: str) -> float:
        value = self._values[key]
        if value is None:
            raise ValueError(f"{key} requires a value")
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

    def table(self, key: str) -> list[dict[str, float]]:
        from packstudio.templates.package_library.core.metal_layers import parse_layers

        return parse_layers(self.text(key))


def _validate_value(item: FieldDefinition, value: TemplateValue) -> None:
    if value is None:
        return
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
