"""Validate the manifest-selected FloTHERM PACK reference dataset."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from lxml import etree
from template_validator import validate_template
from validation_common import (
    iter_strings,
    read_json,
    relative,
    script_check,
    write_json,
)


def validate_catalog(
    data_root: Path,
    template_ids: set[str],
) -> list[str]:
    errors = []
    try:
        catalog = read_json(data_root / "template_catalog.json")
        if catalog.get("template_count") != len(template_ids):
            errors.append("template_catalog.json: template count mismatch")
        if {
            item.get("template_id", item.get("id")) for item in catalog["templates"]
        } != template_ids:
            errors.append("template_catalog.json: template IDs mismatch")
        if any(item.get("status") != "complete" for item in catalog["templates"]):
            errors.append("template_catalog.json: at least one template is incomplete")
        screenshot = data_root / catalog["source"]["screenshot"]
        if not screenshot.is_file() or screenshot.stat().st_size == 0:
            errors.append("template_catalog.json: catalog screenshot is missing")
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        errors.append(f"template_catalog.json: {exc}")
    return errors


def validate_manual_materials(data_root: Path) -> list[str]:
    errors = []
    path = data_root / "materials/materials_manual_captured.json"
    try:
        manual = read_json(path)
        for reference in {
            value for value in iter_strings(manual) if value.lower().endswith(".png")
        }:
            screenshot = data_root / "materials" / reference
            if not screenshot.is_file() or screenshot.stat().st_size == 0:
                errors.append(f"materials_manual_captured.json: missing {reference}")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"materials_manual_captured.json: {exc}")
    return errors


def validate_global_data(
    data_root: Path,
    coverage: dict[str, Any],
    replay: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    errors = []
    json_paths = sorted(data_root.rglob("*.json"))
    for path in json_paths:
        try:
            read_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{relative(path, data_root)}: {exc}")
    for path in [
        data_root / "checkpoint.json",
        data_root / "materials/materials_auto_extracted.json",
        data_root / "materials/materials_manual_captured.json",
        data_root / "materials/master_material_library.json",
        data_root / "internal_property_registry.json",
    ]:
        try:
            if read_json(path).get("status") != "complete":
                errors.append(f"{relative(path, data_root)}: status is not complete")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{relative(path, data_root)}: {exc}")
    try:
        registry = read_json(data_root / "internal_property_registry.json")
        if registry.get("unresolved_required_property_count") != 0:
            errors.append("internal_property_registry.json: unresolved properties remain")
    except (OSError, json.JSONDecodeError):
        pass
    expected_totals = {
        "template_count": len(coverage["templates"]),
        "target_count": sum(item["target_count"] for item in coverage["templates"]),
        "branch_baseline_count": sum(
            item["branch_baseline_count"] for item in coverage["templates"]
        ),
        "variation_count": sum(item["variation_count"] for item in coverage["templates"]),
        "expected_export_count": sum(
            item["expected_export_count"] for item in coverage["templates"]
        ),
    }
    for key, expected in expected_totals.items():
        if coverage.get(key) != expected:
            errors.append(f"parameter_coverage.json: {key} mismatch")
    if replay.get("status") != "complete":
        errors.append("replay_results.json: status is not complete")
    if not replay.get("application_remained_open"):
        errors.append("replay_results.json: application continuity is false")
    ui_states = list(data_root.rglob("ui_states"))
    if ui_states:
        errors.append(
            "redundant ui_states directories exist: "
            + ", ".join(relative(path, data_root) for path in ui_states)
        )
    template_ids = {item["template_id"] for item in coverage["templates"]}
    errors.extend(validate_catalog(data_root, template_ids))
    errors.extend(validate_manual_materials(data_root))
    return {
        "status": "passed" if not errors else "failed",
        "json_file_count": len(json_paths),
        "ui_states_directory_count": len(ui_states),
        "expected_totals": expected_totals,
        "errors": errors,
    }, errors


def finalize_coverage(coverage: dict[str, Any], validated_at: str) -> None:
    coverage["status"] = "complete"
    coverage["validated_at"] = validated_at
    coverage["replay_evidence"] = "validation/replay_results.json"
    for template in coverage["templates"]:
        template["status"] = "complete"
        for target in template["coverage"]:
            if target.get("variation_ids"):
                target["status"] = "replayed_and_analyzed"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "data_root",
        nargs="?",
        type=Path,
        default=Path("flotherm_pack_data"),
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(
            "E:/Program Files/Siemens/SimcenterFlotherm/2504/examples/"
            "FloSCRIPT/Schema/FlopackFloSCRIPTSchema.xsd"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    schema = etree.XMLSchema(etree.parse(str(args.schema)))
    coverage_path = args.data_root / "parameter_coverage.json"
    coverage = read_json(coverage_path)
    replay = read_json(args.data_root / "validation/replay_results.json")
    replay_by_template = {item["template_id"]: item for item in replay["templates"]}
    template_reports = []
    failures = []
    template_dirs = {
        path.name: path for path in (args.data_root / "templates").iterdir() if path.is_dir()
    }
    manifest_ids = {item["template_id"] for item in coverage["templates"]}
    if set(template_dirs) != manifest_ids:
        failures.append("template directory set does not match parameter manifest")
    for template_record in coverage["templates"]:
        template_id = template_record["template_id"]
        validation, template_failures = validate_template(
            template_dirs[template_id],
            template_record,
            replay_by_template.get(template_id),
            args.schema,
            schema,
            validated_at,
        )
        path = template_dirs[template_id] / "validation/validation.json"
        write_json(path, validation)
        template_reports.append(
            {
                "template_id": template_id,
                "status": validation["status"],
                "validation": relative(path, args.data_root),
            }
        )
        failures.extend(f"{template_id}: {item}" for item in template_failures)

    suite_paths = sorted((args.data_root / "validation").glob("*.xml"))
    suite_result, suite_errors = script_check(suite_paths, schema, args.schema, args.data_root)
    failures.extend(f"suite: {error}" for error in suite_errors)
    data_result, data_errors = validate_global_data(args.data_root, coverage, replay)
    failures.extend(f"data_integrity: {error}" for error in data_errors)
    if not failures:
        finalize_coverage(coverage, validated_at)
        write_json(coverage_path, coverage)
    report = {
        "schema_version": "2.0",
        "validated_at": validated_at,
        "software_version": "2504",
        "status": "passed" if not failures else "failed",
        "schema": str(args.schema),
        "summary": {
            "template_count": len(template_reports),
            "passed_template_count": sum(item["status"] == "passed" for item in template_reports),
            "target_count": coverage["target_count"],
            "branch_baseline_count": coverage["branch_baseline_count"],
            "variation_count": coverage["variation_count"],
            "expected_export_count": coverage["expected_export_count"],
            "suite_script_count": len(suite_paths),
        },
        "suite_scripts": suite_result,
        "data_integrity": data_result,
        "templates": template_reports,
        "failures": failures,
    }
    write_json(args.data_root / "validation/report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
