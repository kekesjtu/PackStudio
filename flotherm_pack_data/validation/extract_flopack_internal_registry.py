"""Build an auditable UI-to-FloSCRIPT property registry for PACK 2504."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from flopack_registry_data import COMPONENT_BY_STEP, PROPERTY_BY_LABEL, PROPERTY_OVERRIDES
from registry_field_data import (
    COVERAGE_POLICY_OVERRIDES,
    DROP_IN_SLUG_SYNTHETIC_FIELDS,
    METADATA_FIELDS,
    PROPERTY_TEMPLATE_OVERRIDES,
    TOP_COVER_VARIANT_FIELDS,
    is_material_field,
    option_values,
)
from registry_sources import (
    AUTHENTIC_RECORDING_GLOBS,
    binary_tokens,
    recorded_commands,
)

DATA_ROOT = Path(__file__).resolve().parents[1]
INSTALL_BIN = Path("E:/Program Files/Siemens/SimcenterFlotherm/2504/WinXP/bin")
STRINGS_EXE = Path("E:/msys64/ucrt64/bin/strings.exe")
DLLS = [INSTALL_BIN / "flopackdatasets.dll", INSTALL_BIN / "flopackproperties.dll"]
NON_SCALAR_CONTROLS = {"button", "matrix_editor_button", "table"}
READ_ONLY_CONTROLS = {"read_only_single_option"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def classify(name: str, control: str, default: Any, scope: str) -> tuple[str, str]:
    if name == "JEDEC Footprint":
        return "jedec_preset", "three_representative_values_including_default"
    if name in METADATA_FIELDS:
        return "metadata", "not_model_input"
    if is_material_field(name):
        return "material", "default_only"
    if control in NON_SCALAR_CONTROLS:
        return "editor_or_table", "separate_representative_editor_case"
    if control in READ_ONLY_CONTROLS:
        return "read_only", "no_variation"
    if control in {"text", "multiline_text"}:
        return "metadata", "not_model_input"
    if control == "checkbox":
        return "boolean_option", "alternate_value"
    if control == "select":
        return "enum_option", "all_non_default_values"
    if control in {"number", "number_with_unit", "integer", "integer_spinbox"}:
        policy = "low_and_high" if default is not None else "conditional_low_and_high"
        return "numeric_parameter", policy
    return "unclassified", "manual_review"


def property_for(template_id: str, component: str | None, field: dict[str, Any]) -> str | None:
    if field.get("property"):
        return field["property"]
    if field.get("property_by_package_type"):
        return next(iter(field["property_by_package_type"].values()))
    label = field["name"]
    template_override = PROPERTY_TEMPLATE_OVERRIDES.get((template_id, component, label))
    if template_override:
        return template_override
    return PROPERTY_OVERRIDES.get((component, label), PROPERTY_BY_LABEL.get(label))


def evidence_for(
    scope: str,
    component: str | None,
    prop: str | None,
    tokens: set[str],
    starters: dict[str, set[str]],
    modified: dict[tuple[str, str], set[str]],
) -> tuple[list[str], list[str]]:
    evidence: list[str] = []
    observed: set[str] = set()
    if not prop:
        return evidence, []
    if scope == "starter" and prop in starters:
        evidence.append("recorded_new_package")
        observed.update(starters[prop])
    if component and (component, prop) in modified:
        evidence.append("recorded_modify_component")
        observed.update(modified[(component, prop)])
    if prop in tokens:
        evidence.append("installed_dll_ascii_string")
    if not evidence:
        evidence.append("curated_binary_disassembly_mapping")
    return evidence, sorted(observed)


def make_entry(
    template_id: str,
    scope: str,
    location: str,
    component: str | None,
    field: dict[str, Any],
    tokens: set[str],
    starters: dict[str, set[str]],
    modified: dict[tuple[str, str], set[str]],
) -> dict[str, Any]:
    name = field["name"]
    control = field["control"]
    default = field.get("default")
    classification, policy = classify(name, control, default, scope)
    override = COVERAGE_POLICY_OVERRIDES.get(
        (template_id, location, name)
    ) or COVERAGE_POLICY_OVERRIDES.get((template_id, location, "*"))
    if override:
        classification = override["classification"]
        policy = override["coverage_policy"]
    prop = property_for(template_id, component, field)
    evidence, observed = evidence_for(scope, component, prop, tokens, starters, modified)
    required = classification not in {
        "metadata",
        "editor_or_table",
        "read_only",
        "inactive_default_material_branch",
    } and not (classification == "material" and name.endswith("Group"))
    status = "resolved" if prop else ("not_applicable" if not required else "unresolved")
    entry = {
        "target_id": f"{template_id}.{location}.{name}",
        "scope": scope,
        "ui_location": location,
        "component": component,
        "label": name,
        "control": control,
        "default": default,
        "options": option_values(field),
        "classification": classification,
        "coverage_policy": policy,
        "property_name": prop,
        "property_status": status,
        "evidence": evidence,
        "observed_recorded_values": observed,
    }
    for dependency in ("visible_when", "enabled_when", "hidden_when"):
        if dependency in field:
            entry[dependency] = field[dependency]
    if override:
        entry["coverage_reason"] = override["reason"]
    return entry


def synthetic_top_cover(template_id: str) -> list[tuple[str, dict[str, Any]]]:
    if template_id not in {"flip_chip_cbga", "flip_chip_pbga"}:
        return []
    fields = []
    for variant, specs in TOP_COVER_VARIANT_FIELDS.items():
        for name, control, default in specs:
            field: dict[str, Any] = {"name": name, "control": control, "default": default}
            if name == "Stiffener":
                field["options"] = ["no", "yes"]
            fields.append((variant, field))
    return fields


def build_template(
    ui_path: Path,
    tokens: set[str],
    starters: dict[str, set[str]],
    modified: dict[tuple[str, str], set[str]],
) -> dict[str, Any]:
    ui = read_json(ui_path)
    template_id = ui["template_id"]
    entries = []
    for field in ui.get("starter_fields", []):
        entries.append(
            make_entry(template_id, "starter", "starter", None, field, tokens, starters, modified)
        )
    for step in ui.get("steps", []):
        component = COMPONENT_BY_STEP.get(step["id"])
        for field in step.get("fields", []):
            entries.append(
                make_entry(
                    template_id,
                    "component",
                    step["id"],
                    component,
                    field,
                    tokens,
                    starters,
                    modified,
                )
            )
    for variant, field in synthetic_top_cover(template_id):
        entry = make_entry(
            template_id,
            "synthetic_component_variant",
            f"top_cover.{variant}",
            "topCover",
            field,
            tokens,
            starters,
            modified,
        )
        entry["branch_condition"] = {"topCover": "lid" if variant == "lid_stiffener" else variant}
        if variant == "lid_stiffener":
            entry["branch_condition"]["stiffener"] = "yes"
        entries.append(entry)
    if template_id == "flip_chip_pbga":
        for name, control, default in DROP_IN_SLUG_SYNTHETIC_FIELDS:
            entries.append(
                make_entry(
                    template_id,
                    "synthetic_component_variant",
                    "drop_in_slug.encapsulant",
                    "dropInSlug",
                    {"name": name, "control": control, "default": default},
                    tokens,
                    starters,
                    modified,
                )
            )
    unresolved = [item["target_id"] for item in entries if item["property_status"] == "unresolved"]
    policies = defaultdict(int)
    for entry in entries:
        policies[entry["coverage_policy"]] += 1
    return {
        "template_id": template_id,
        "status": "complete" if not unresolved else "needs_review",
        "entry_count": len(entries),
        "coverage_policy_counts": dict(sorted(policies.items())),
        "unresolved_required_properties": unresolved,
        "entries": entries,
    }


def main() -> int:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    tokens = binary_tokens(DLLS, STRINGS_EXE)
    starters, modified = recorded_commands(DATA_ROOT)
    templates = [
        build_template(path, tokens, starters, modified)
        for path in sorted((DATA_ROOT / "templates").glob("*/ui.json"))
    ]
    unresolved = sum(len(item["unresolved_required_properties"]) for item in templates)
    registry = {
        "schema_version": "2.0",
        "software_version": "2504",
        "generated_at": generated_at,
        "status": "complete" if not unresolved else "needs_review",
        "sources": {
            "dlls": [str(path) for path in DLLS],
            "strings_tool": str(STRINGS_EXE),
            "ui_glob": "templates/*/ui.json",
            "recorded_floscript_globs": list(AUTHENTIC_RECORDING_GLOBS),
        },
        "method": (
            "Recorded FloSCRIPT is preferred; installed DLL strings and curated "
            "disassembly mappings fill fields not changed during UI capture."
        ),
        "template_count": len(templates),
        "entry_count": sum(item["entry_count"] for item in templates),
        "unresolved_required_property_count": unresolved,
        "templates": templates,
    }
    output = DATA_ROOT / "internal_property_registry.json"
    output.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "status": registry["status"],
                "templates": len(templates),
                "entries": registry["entry_count"],
                "unresolved": unresolved,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if not unresolved else 1


if __name__ == "__main__":
    raise SystemExit(main())
