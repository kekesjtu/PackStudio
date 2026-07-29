"""Generate constraint-aware comprehensive FloSCRIPT sweeps from the registry."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from floscript_generation import (
    baseline_definition,
    combined_suite,
    make_script,
    numeric_values,
    relative,
    slug,
    write_xml,
)
from lxml import etree
from sweep_generation_helpers import (
    ACTIONABLE_POLICIES,
    branch_value,
    dependent_starter_changes,
    make_config,
    read_json,
    replace_target,
    select_targets,
    variation_identifier,
    variation_values,
    write_json,
)
from sweep_strategy import (
    context_for,
    floxml_effect_expectation,
    numeric_value_override,
    prerequisite_context_needed,
)

DATA_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = Path(
    "E:/Program Files/Siemens/SimcenterFlotherm/2504/examples/"
    "FloSCRIPT/Schema/FlopackFloSCRIPTSchema.xsd"
)


def create_template_sweeps(
    template_registry: dict[str, Any],
) -> tuple[dict[str, Any], Path, list[Path]]:
    template_id = template_registry["template_id"]
    template_dir = DATA_ROOT / "templates" / template_id
    ui = read_json(template_dir / "ui.json")
    package_type, starter_values = baseline_definition(template_dir / "baseline/script.xml")
    targets, aliases = select_targets(template_registry)
    script_paths: list[Path] = []
    coverage_records = []
    counters: defaultdict[str, int] = defaultdict(int)
    branch_counter = 0
    for entry in targets:
        component = entry.get("component")
        prop = entry["property_name"]
        effect = floxml_effect_expectation(
            template_id,
            "new_package" if entry["scope"] == "starter" else component,
            prop,
        )
        context = context_for(template_id, component or "", prop, entry["ui_location"])
        values, baseline_value = variation_values(entry, ui)
        if entry["coverage_policy"] == "conditional_low_and_high":
            baseline_value = branch_value(entry, context)
            integer = entry["control"] in {"integer", "integer_spinbox"}
            values = numeric_values(baseline_value, integer)
        override_values, value_selection_reason = numeric_value_override(
            template_id, component, prop
        )
        if override_values is not None:
            values = override_values
        branch_needed = (
            entry["scope"] != "starter"
            and bool(context)
            and prerequisite_context_needed(component, prop, entry["ui_location"], entry["default"])
        )
        comparison = template_dir / "baseline/model.xml"
        branch_commands: list[tuple[str, str, Any]] = []
        if branch_needed:
            branch_counter += 1
            branch_id = f"br_v2_{slug(component)}_{slug(prop)}"
            branch_dir = template_dir / "validation/branch_baselines" / branch_id
            branch_commands = replace_target(context, component, prop, baseline_value)
            branch_script = branch_dir / "script.xml"
            comparison = branch_dir / "model.xml"
            write_xml(
                make_script(
                    package_type,
                    starter_values,
                    comparison,
                    branch_commands,
                ),
                branch_script,
            )
            script_paths.append(branch_script)
        variation_ids = []
        for value in values:
            kind = entry["classification"]
            counters[kind] += 1
            variation_id = variation_identifier(kind, counters[kind], entry, value)
            category = "param_sweeps" if kind == "numeric_parameter" else "option_switches"
            variation_dir = template_dir / "xml_variations" / category / variation_id
            model_path = variation_dir / "model.xml"
            script_path = variation_dir / "script.xml"
            dependent: dict[str, Any] = {}
            starter_changes = None
            starter_remove = None
            commands = replace_target(branch_commands, component, prop, value)
            if entry["scope"] == "starter":
                starter_changes, starter_remove, dependent = dependent_starter_changes(
                    entry, value, ui
                )
                commands = []
            write_xml(
                make_script(
                    package_type,
                    starter_values,
                    model_path,
                    commands,
                    starter_changes,
                    starter_remove,
                ),
                script_path,
            )
            config = make_config(
                DATA_ROOT,
                template_id,
                variation_id,
                entry,
                baseline_value,
                value,
                comparison,
                dependent,
                branch_commands,
            )
            if value_selection_reason:
                config["value_selection_reason"] = value_selection_reason
            if effect:
                config["floxml_effect_expectation"] = effect
            write_json(variation_dir / "config.json", config)
            script_paths.append(script_path)
            variation_ids.append(variation_id)
        coverage_records.append(
            {
                "target_id": entry["target_id"],
                "component": "new_package" if entry["scope"] == "starter" else component,
                "property": prop,
                "label": entry["label"],
                "policy": entry["coverage_policy"],
                "baseline": baseline_value,
                "planned_values": values,
                "comparison_baseline": relative(comparison, template_dir),
                "variation_ids": variation_ids,
                "status": "scripts_generated_pending_replay",
                **(
                    {"value_selection_reason": value_selection_reason}
                    if value_selection_reason
                    else {}
                ),
                **({"floxml_effect_expectation": effect} if effect else {}),
            }
        )
    for entry in template_registry["entries"]:
        if entry["target_id"] in aliases:
            status = "duplicate_ui_alias"
        elif entry["coverage_policy"] not in ACTIONABLE_POLICIES:
            status = entry["coverage_policy"]
        else:
            continue
        coverage_records.append(
            {
                "target_id": entry["target_id"],
                "component": entry.get("component"),
                "property": entry.get("property_name"),
                "label": entry["label"],
                "policy": entry["coverage_policy"],
                "status": status,
            }
        )
    suite = DATA_ROOT / "validation" / f"comprehensive_replay_{template_id}.xml"
    export_count = combined_suite(script_paths, suite)
    result = {
        "template_id": template_id,
        "status": "scripts_generated_pending_replay",
        "target_count": len(targets),
        "branch_baseline_count": branch_counter,
        "variation_count": sum(len(item.get("variation_ids", [])) for item in coverage_records),
        "expected_export_count": export_count,
        "suite": relative(suite, DATA_ROOT),
        "coverage": coverage_records,
    }
    return result, suite, [*script_paths, suite]


def main() -> int:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    registry = read_json(DATA_ROOT / "internal_property_registry.json")
    template_results = []
    suite_paths = []
    generated_scripts = []
    for template in registry["templates"]:
        result, suite, scripts = create_template_sweeps(template)
        template_results.append(result)
        suite_paths.append(suite)
        generated_scripts.extend(scripts)
    global_suite = DATA_ROOT / "validation/comprehensive_replay_suite.xml"
    expected_exports = combined_suite(suite_paths, global_suite)
    generated_scripts.append(global_suite)
    schema = etree.XMLSchema(etree.parse(str(SCHEMA_PATH)))
    generated_scripts = sorted(set(generated_scripts))
    for path in generated_scripts:
        schema.assertValid(etree.parse(str(path)))
    coverage = {
        "schema_version": "2.0",
        "software_version": "2504",
        "generated_at": generated_at,
        "status": "scripts_generated_pending_replay",
        "strategy": {
            "jedec": "three representative values per applicable template, including baseline",
            "materials": "default_only",
            "numeric": (
                "0.9x and 1.1x; constrained integers use valid neighboring "
                "values when PACK normalizes n-1 or n+1"
            ),
            "options": "every non-default value",
            "conditional": "safe branch baseline, then one target changes per comparison",
            "inactive_material_branches": (
                "recorded but not swept when defaults are No Attachment and "
                "activation would require a non-default material"
            ),
            "non_scalar_editors": "documented separately; no scalar sweep is fabricated",
        },
        "template_count": len(template_results),
        "target_count": sum(item["target_count"] for item in template_results),
        "branch_baseline_count": sum(item["branch_baseline_count"] for item in template_results),
        "variation_count": sum(item["variation_count"] for item in template_results),
        "expected_export_count": expected_exports,
        "xsd_validated_script_count": len(generated_scripts),
        "global_suite": relative(global_suite, DATA_ROOT),
        "templates": template_results,
    }
    write_json(DATA_ROOT / "parameter_coverage.json", coverage)
    print(
        json.dumps(
            {
                "status": coverage["status"],
                "templates": coverage["template_count"],
                "targets": coverage["target_count"],
                "branches": coverage["branch_baseline_count"],
                "variations": coverage["variation_count"],
                "exports": expected_exports,
                "xsd_validated_scripts": len(generated_scripts),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
