"""Selection, value, and manifest helpers for comprehensive PACK sweeps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from floscript_generation import internal_value, numeric_values, relative, slug
from sweep_strategy import seed_from_context

ACTIONABLE_POLICIES = {
    "alternate_value",
    "all_non_default_values",
    "low_and_high",
    "conditional_low_and_high",
    "three_representative_values_including_default",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def target_key(entry: dict[str, Any]) -> tuple[str, str]:
    prop = entry["property_name"]
    if prop in {"topCover", "substrateLayer", "includeSlug"}:
        return "shared", prop
    return entry.get("component") or "new_package", prop


def preferred(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    prop = left["property_name"]
    if prop in {"topCover", "substrateLayer"}:
        return left if left["scope"] == "starter" else right
    if prop == "includeSlug":
        return left if left["scope"] != "starter" else right
    return left


def select_targets(
    template: dict[str, Any],
) -> tuple[list[dict[str, Any]], set[str]]:
    selected: dict[tuple[str, str], dict[str, Any]] = {}
    aliases: set[str] = set()
    for entry in template["entries"]:
        if entry["coverage_policy"] not in ACTIONABLE_POLICIES:
            continue
        key = target_key(entry)
        if key not in selected:
            selected[key] = entry
            continue
        winner = preferred(selected[key], entry)
        loser = entry if winner is selected[key] else selected[key]
        aliases.add(loser["target_id"])
        selected[key] = winner
    return list(selected.values()), aliases


def starter_field(ui: dict[str, Any], label: str) -> dict[str, Any]:
    return next(item for item in ui["starter_fields"] if item["name"] == label)


def jedec_values(entry: dict[str, Any], ui: dict[str, Any]) -> list[Any]:
    field = starter_field(ui, "JEDEC Footprint")
    if field.get("options"):
        options = field["options"]
    else:
        baseline_prop = entry["property_name"]
        package_type = next(
            key for key, prop in field["property_by_package_type"].items() if prop == baseline_prop
        )
        options = field["options_by_package_type"][package_type]
    chosen = [entry["default"], options[len(options) // 2], options[-1]]
    unique = []
    for value in chosen + options:
        if value not in unique:
            unique.append(value)
        if len(unique) == 3:
            break
    return unique


def variation_values(
    entry: dict[str, Any],
    ui: dict[str, Any],
) -> tuple[list[Any], Any]:
    policy = entry["coverage_policy"]
    default = internal_value(entry["default"])
    if policy == "three_representative_values_including_default":
        selected = jedec_values(entry, ui)
        return [value for value in selected if value != entry["default"]], default
    if policy == "alternate_value":
        return [not bool(entry["default"])], default
    if policy == "all_non_default_values":
        options = [internal_value(value) for value in entry["options"]]
        return [value for value in options if value != default], default
    if policy == "low_and_high":
        integer = entry["control"] in {"integer", "integer_spinbox"}
        return numeric_values(entry["default"], integer), entry["default"]
    return [], None


def dependent_starter_changes(
    entry: dict[str, Any],
    value: Any,
    ui: dict[str, Any],
) -> tuple[dict[str, Any], set[str], dict[str, Any]]:
    changes = {entry["property_name"]: value}
    remove: set[str] = set()
    dependent: dict[str, Any] = {}
    prop = entry["property_name"]
    if prop not in {"pqfpPackageType", "sopPackageType"}:
        return changes, remove, dependent
    field = starter_field(ui, "JEDEC Footprint")
    remove.update(field["property_by_package_type"].values())
    footprint_prop = field["property_by_package_type"][value]
    footprint = field["options_by_package_type"][value][0]
    changes[footprint_prop] = footprint
    dependent[footprint_prop] = footprint
    return changes, remove, dependent


def replace_target(
    commands: list[tuple[str, str, Any]],
    component: str,
    prop: str,
    value: Any,
) -> list[tuple[str, str, Any]]:
    result = [item for item in commands if item[:2] != (component, prop)]
    result.append((component, prop, value))
    return result


def branch_value(
    entry: dict[str, Any],
    context: list[tuple[str, str, Any]],
) -> Any:
    if entry["default"] is not None:
        return internal_value(entry["default"])
    value = seed_from_context(context, entry["component"], entry["property_name"])
    if value is None:
        raise ValueError(f"No safe conditional seed for {entry['target_id']}")
    return value


def variation_identifier(
    kind: str,
    index: int,
    entry: dict[str, Any],
    value: Any,
) -> str:
    prefix = (
        "par_v2"
        if kind == "numeric_parameter"
        else "jed_v2"
        if kind == "jedec_preset"
        else "opt_v2"
    )
    return f"{prefix}_c{index:03d}_{slug(entry['property_name'], 28)}_{slug(value, 22)}"


def make_config(
    data_root: Path,
    template_id: str,
    variation_id: str,
    entry: dict[str, Any],
    baseline: Any,
    value: Any,
    comparison: Path,
    dependent: dict[str, Any],
    branch_commands: list[tuple[str, str, Any]],
) -> dict[str, Any]:
    component = "new_package" if entry["scope"] == "starter" else entry["component"]
    return {
        "schema_version": "2.0",
        "template_id": template_id,
        "variation_id": variation_id,
        "kind": entry["classification"],
        "coverage_policy": entry["coverage_policy"],
        "target": {
            "component": component,
            "property": entry["property_name"],
            "label": entry["label"],
            "baseline": baseline,
            "value": value,
        },
        "comparison_baseline": relative(comparison, data_root / "templates" / template_id),
        "branch_preconditions": [
            {"component": item[0], "property": item[1], "value": item[2]}
            for item in branch_commands
            if item[:2] != (entry.get("component"), entry["property_name"])
        ],
        "required_dependent_initialization": dependent,
        "single_variable_relative_to_comparison_baseline": True,
        "material_policy": "default_only",
        "property_evidence": entry["evidence"],
        "execution_status": "pending_replay",
    }
