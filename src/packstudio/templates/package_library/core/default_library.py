"""Build wizard definitions from serialized defaults and verified PACK references."""

from pydantic import TypeAdapter

from packstudio.default_parameters import read_defaults
from packstudio.templates.package_library.core.definitions import (
    FieldDefinition,
    MaterialSelectionDefinition,
    PresetOption,
    _validate_value,
)


def template_defaults(template_id: str) -> dict:
    payload = read_defaults(f"templates/{template_id}.json", "packstudio.template-defaults/v1")
    if payload["template_id"] != template_id:
        raise ValueError(f"default parameter template mismatch: {template_id}")
    return payload


def _preset(payload: dict) -> PresetOption:
    values = payload["values"].copy()
    if "source" in payload:
        source = payload["source"]
        family = read_defaults(
            f"flotherm/{source['family']}.json", "packstudio.flotherm-presets/v1"
        )
        record = next((item for item in family["records"] if item["id"] == source["preset"]), None)
        if record is None:
            raise ValueError(f"missing PACK preset {source}")
        for key, symbol in payload["source_values"].items():
            value = record["values"][symbol]
            if value is None:
                raise ValueError(f"unresolved PACK value {source}/{symbol}")
            values[key] = value
    return TypeAdapter(PresetOption).validate_python(
        {"value": payload["value"], "label": payload["label"], "values": values}
    )


def load_fields(template_id: str) -> tuple[FieldDefinition, ...]:
    items = []
    for payload in template_defaults(template_id)["fields"]:
        payload["presets"] = tuple(_preset(preset) for preset in payload["presets"])
        item = TypeAdapter(FieldDefinition).validate_python(payload)
        _validate_value(item, item.default)
        if item.presets and tuple(preset.value for preset in item.presets) != item.options:
            raise ValueError(f"preset options mismatch: {template_id}/{item.key}")
        items.append(item)
    fields = {item.key: item for item in items}
    if len(fields) != len(items):
        raise ValueError(f"duplicate default parameter fields in {template_id}")
    for item in items:
        for preset in item.presets:
            for key, value in preset.values.items():
                if key not in fields:
                    raise ValueError(f"unknown preset parameter {template_id}/{key}")
                _validate_value(fields[key], value)
    return tuple(items)


def load_material_selections(template_id: str) -> tuple[MaterialSelectionDefinition, ...]:
    items = TypeAdapter(tuple[MaterialSelectionDefinition, ...]).validate_python(
        template_defaults(template_id)["material_selections"]
    )
    for item in items:
        if item.default not in item.options:
            raise ValueError(f"invalid material default {template_id}/{item.group_id}")
    return items
