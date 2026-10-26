"""Build wizard definitions from serialized defaults and verified PACK references."""

from dataclasses import replace

from pydantic import TypeAdapter

from packstudio.runtime_data import read_defaults
from packstudio.templates.package_library.core.definitions import (
    FieldDefinition,
    MaterialSelectionDefinition,
    PresetOption,
    _validate_value,
)
from packstudio.templates.package_library.core.materials import material, material_id_for_name
from packstudio.templates.package_library.core.native_presets import expand_native_presets

_PRESET_ADAPTER = TypeAdapter(PresetOption)
_FIELD_ADAPTER = TypeAdapter(FieldDefinition)
_MATERIAL_SELECTION_ADAPTER = TypeAdapter(tuple[MaterialSelectionDefinition, ...])


def template_defaults(template_id: str) -> dict:
    payload = read_defaults(f"templates/{template_id}.json", "packstudio.template-defaults/v1")
    if payload["template_id"] != template_id:
        raise ValueError(f"default parameter template mismatch: {template_id}")
    return payload


def _preset(payload: dict, representation: str) -> PresetOption:
    return _PRESET_ADAPTER.validate_python(
        {
            "value": payload["value"],
            "label": payload["label"],
            "values": payload["values"],
            "bga": {**payload["bga"], "representation": representation}
            if payload.get("bga") is not None else None,
            "metadata": payload.get("metadata", {}),
            "material_assignments": payload.get("material_assignments", {}),
        }
    )


def load_fields(template_id: str) -> tuple[FieldDefinition, ...]:
    items = []
    defaults = template_defaults(template_id)
    serialized = defaults["fields"]
    footprint = next(item for item in serialized if item["control"] == "footprint")
    expanded = expand_native_presets(template_id, footprint, serialized)
    selected = next(p for p in expanded["presets"] if p["value"] == footprint["default"])
    for payload in serialized:
        if payload["control"] == "footprint":
            payload = expanded
        elif payload["key"] in selected["values"]:
            payload["default"] = selected["values"][payload["key"]]
        payload.setdefault("default", None)
        payload["presets"] = tuple(
            _preset(preset, defaults["default_bga_representation"]) for preset in payload["presets"]
        )
        item = _FIELD_ADAPTER.validate_python(payload)
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
    footprint = next(item for item in items if item.control == "footprint")
    selected = next(p for p in footprint.presets if p.value == footprint.default)
    return tuple(
        replace(item, default=selected.values.get(item.key, item.default)) for item in items
    )


def load_material_selections(
    template_id: str, fields: tuple[FieldDefinition, ...] | None = None
) -> tuple[MaterialSelectionDefinition, ...]:
    items = _MATERIAL_SELECTION_ADAPTER.validate_python(
        template_defaults(template_id)["material_selections"]
    )
    if fields is None:
        fields = load_fields(template_id)
    footprint = next(item for item in fields if item.control == "footprint")
    selected = next(p for p in footprint.presets if p.value == footprint.default)
    items = tuple(
        replace(
            item,
            default=selected.material_assignments.get(
                item.group_id, material_id_for_name(material(item.default).name)
            ),
            options=tuple(
                dict.fromkeys(
                    (
                        *(
                            material_id_for_name(material(identifier).name)
                            for identifier in item.options
                        ),
                        *(
                            p.material_assignments[item.group_id]
                            for p in footprint.presets
                            if item.group_id in p.material_assignments
                        ),
                    )
                )
            ),
        )
        for item in items
    )
    for item in items:
        if item.default not in item.options:
            raise ValueError(f"invalid material default {template_id}/{item.group_id}")
    return items
