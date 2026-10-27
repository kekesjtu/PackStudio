from __future__ import annotations

from typing import TYPE_CHECKING, Any

from packstudio.templates.package_library.core.step_labels import step_label

if TYPE_CHECKING:
    from packstudio.templates.package_library.core.definitions import (
        FieldDefinition,
        TemplateDefinition,
    )


def build_wizard_schema(definition: TemplateDefinition) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in definition.fields:
        supported = list(item.options)
        if not supported and item.minimum is not None and item.maximum is not None:
            supported = [item.minimum, item.maximum]
        grouped.setdefault(item.step, []).append(
            {
                "target_id": item.target_id(definition.id),
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
                            f"{definition.id}.{key}": value for key, value in preset.values.items()
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
                "preset_materials": {p.value: p.material_assignments for p in item.presets} or None,
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
    for item in definition.material_selections:
        grouped.setdefault(item.step, []).append(
            {
                "target_id": item.target_id(definition.id),
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
        *[step for step in definition.step_order if step in grouped],
        *[step for step in grouped if step not in definition.step_order],
    ]
    return {
        "schema_version": "packstudio.wizard/v2",
        "template_id": definition.id,
        "steps": [
            {"id": step, "label": step_label(step), "fields": items}
            for step in ordered_steps
            for items in (grouped[step],)
        ],
        "has_bga": definition.has_bga,
        "special_rules": {
            "outline_type": "standard_outline",
            "die_type": "actual_type",
            "bga_pattern": (
                "implicit_full_with_center_and_removal" if definition.has_bga else None
            ),
            "flip_chip_bumps": ("thick_isotropic_equivalent" if definition.has_flip_chip else None),
        },
    }


def _classification(item: FieldDefinition) -> str:
    if item.control == "footprint":
        return "jedec_preset"
    if item.control == "checkbox":
        return "boolean_option"
    if item.control in {"number", "integer", "integer_spinbox"}:
        return "numeric_parameter"
    return "enum_option"
