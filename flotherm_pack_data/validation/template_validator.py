"""Per-template checks used by the reference-data validator."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

from floxml_diff_core import analyze, sha256
from lxml import etree
from validation_common import (
    iter_strings,
    manifest_variations,
    read_json,
    relative,
    replay_check,
    script_check,
)


def baseline_replay_check(
    template_dir: Path,
) -> tuple[dict[str, Any], list[str]]:
    baseline = template_dir / "baseline/model.xml"
    replay = template_dir / "validation/baseline_replay_model.xml"
    failures = []
    result: dict[str, Any] = {
        "status": "failed",
        "script": "baseline/script.xml",
        "output": "validation/baseline_replay_model.xml",
        "application_remained_open": True,
    }
    try:
        diff = analyze(baseline, replay)
        baseline_hash = sha256(baseline)
        replay_hash = sha256(replay)
        if baseline_hash == replay_hash:
            comparison = "byte_identical"
        elif not diff["semantic_change"]:
            comparison = "semantic_identical_numeric_formatting_only"
        else:
            comparison = "semantic_difference"
            failures.append("baseline_replay: replay differs semantically")
        result.update(
            {
                "status": "passed" if not failures else "failed",
                "comparison": comparison,
                "baseline_sha256": baseline_hash,
                "replay_sha256": replay_hash,
                "semantic_change": diff["semantic_change"],
                "numeric_formatting_differences_ignored": True,
            }
        )
    except (OSError, ET.ParseError) as exc:
        failures.append(f"baseline_replay: {exc}")
        result["error"] = str(exc)
    return result, failures


def variation_checks(
    template_dir: Path,
    template_record: dict[str, Any],
) -> tuple[dict[str, Any], list[str], list[Path], list[Path]]:
    failures = []
    results = []
    model_paths = []
    script_paths = []
    kinds: Counter[str] = Counter()
    expected_ids = {
        variation_id
        for target in template_record["coverage"]
        for variation_id in target.get("variation_ids", [])
    }
    for target, directory, config in manifest_variations(template_dir, template_record):
        variation_id = directory.name
        model = directory / "model.xml"
        script = directory / "script.xml"
        diff_path = directory / "diff_xml.json"
        baseline = template_dir / target["comparison_baseline"]
        errors = []
        model_paths.append(model)
        script_paths.append(script)
        try:
            diff = read_json(diff_path)
            kinds[config["kind"]] += 1
            if config["template_id"] != template_dir.name:
                errors.append("config template_id mismatch")
            if config["variation_id"] != variation_id:
                errors.append("config variation_id mismatch")
            if config["comparison_baseline"] != target["comparison_baseline"]:
                errors.append("config comparison_baseline mismatch")
            if config["target"]["property"] != target["property"]:
                errors.append("config target property mismatch")
            if config.get("material_policy") != "default_only":
                errors.append("config material policy is not default_only")
            if not config.get("single_variable_relative_to_comparison_baseline"):
                errors.append("single-variable declaration is false")
            expectation = config.get("floxml_effect_expectation")
            accepted_no_effect = (
                not diff["semantic_change"]
                and expectation
                and diff.get("outcome") == "accepted_no_floxml_effect"
            )
            if not diff["semantic_change"] and not accepted_no_effect:
                errors.append("unexpected semantic_change false")
            if diff.get("floxml_effect_expectation") != expectation:
                errors.append("FloXML effect expectation mismatch")
            if diff["comparison"]["baseline_sha256"] != sha256(baseline):
                errors.append("comparison-baseline SHA-256 mismatch")
            if diff["comparison"]["variation_sha256"] != sha256(model):
                errors.append("variation SHA-256 mismatch")
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            diff = {}
            errors.append(str(exc))
        failures.extend(f"{variation_id}: {error}" for error in errors)
        results.append(
            {
                "variation_id": variation_id,
                "kind": config.get("kind"),
                "target": config.get("target"),
                "comparison_baseline": target["comparison_baseline"],
                "status": "passed" if not errors else "failed",
                "semantic_change": diff.get("semantic_change"),
                "outcome": diff.get("outcome"),
                "summary": diff.get("summary"),
                "errors": errors,
            }
        )

    summary_path = template_dir / "xml_variations.json"
    summary_errors = []
    try:
        summary = read_json(summary_path)
        summary_ids = {item["variation_id"] for item in summary["variations"]}
        if summary.get("status") != "complete":
            summary_errors.append("status is not complete")
        if summary.get("variation_count") != template_record["variation_count"]:
            summary_errors.append("variation_count mismatch")
        if summary_ids != expected_ids:
            summary_errors.append("variation ID set mismatch")
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        summary_errors.append(str(exc))
    failures.extend(f"xml_variations.json: {error}" for error in summary_errors)
    check = {
        "status": "passed" if not failures else "failed",
        "variation_count": len(results),
        "expected_variation_count": template_record["variation_count"],
        "kind_counts": dict(sorted(kinds.items())),
        "manifest_selected_only": True,
        "summary_errors": summary_errors,
        "variations": results,
    }
    return check, failures, model_paths, script_paths


def structured_checks(template_dir: Path) -> tuple[dict[str, Any], list[str]]:
    template_id = template_dir.name
    paths = [
        template_dir / "template.json",
        template_dir / "ui.json",
        template_dir / "baseline/params.json",
        template_dir / "xml_variations.json",
    ]
    errors = []
    ui: dict[str, Any] = {}
    try:
        template = read_json(paths[0])
        ui = read_json(paths[1])
        read_json(paths[2])
        if template.get("template_id") != template_id:
            errors.append("template.json template_id mismatch")
        if template.get("capture_status") != "complete":
            errors.append("template.json capture_status is not complete")
        if ui.get("template_id") != template_id:
            errors.append("ui.json template_id mismatch")
        if ui.get("capture_status") != "complete":
            errors.append("ui.json capture_status is not complete")
        if not ui.get("steps"):
            errors.append("ui.json has no captured steps")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
    return {
        "status": "passed" if not errors else "failed",
        "files": [relative(path, template_dir) for path in paths],
        "errors": errors,
        "_ui": ui,
    }, errors


def screenshot_checks(
    template_dir: Path,
    ui: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    screenshots = sorted((template_dir / "screenshots").glob("*.png"))
    errors = []
    if not screenshots:
        errors.append("no screenshots captured")
    errors.extend(
        f"{relative(path, template_dir)} is empty"
        for path in screenshots
        if path.stat().st_size == 0
    )
    references = sorted({value for value in iter_strings(ui) if value.lower().endswith(".png")})
    for reference in references:
        path = template_dir / reference
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing UI screenshot reference: {reference}")
    return {
        "status": "passed" if not errors else "failed",
        "file_count": len(screenshots),
        "referenced_file_count": len(references),
        "errors": errors,
    }, errors


def validate_template(
    template_dir: Path,
    template_record: dict[str, Any],
    replay_record: dict[str, Any] | None,
    schema_path: Path,
    schema: etree.XMLSchema,
    validated_at: str,
) -> tuple[dict[str, Any], list[str]]:
    failures = []
    variation_check, errors, variation_models, variation_scripts = variation_checks(
        template_dir, template_record
    )
    failures.extend(errors)
    branch_models = sorted(
        {
            template_dir / target["comparison_baseline"]
            for target in template_record["coverage"]
            if target.get("comparison_baseline") not in {None, "baseline/model.xml"}
        }
    )
    branch_scripts = [path.parent / "script.xml" for path in branch_models]
    if len(branch_models) != template_record["branch_baseline_count"]:
        failures.append("branch baseline count mismatch")
    script_groups = {
        "baseline_script_xsd": [template_dir / "baseline/script.xml"],
        "recording_logs_xsd": sorted((template_dir / "logs").glob("*.xml")),
        "branch_scripts_xsd": branch_scripts,
        "variation_scripts_xsd": variation_scripts,
    }
    script_results = {}
    for name, paths in script_groups.items():
        result, errors = script_check(paths, schema, schema_path, template_dir)
        script_results[name] = result
        failures.extend(f"{name}: {error}" for error in errors)
    floxml_paths = [
        template_dir / "baseline/model.xml",
        template_dir / "validation/baseline_replay_model.xml",
        *branch_models,
        *variation_models,
    ]
    floxml_errors = []
    for path in floxml_paths:
        try:
            ET.parse(path)
        except (OSError, ET.ParseError) as exc:
            floxml_errors.append(f"{relative(path, template_dir)}: {exc}")
    failures.extend(f"floxml_well_formed: {error}" for error in floxml_errors)
    baseline_check, errors = baseline_replay_check(template_dir)
    failures.extend(errors)
    structured, errors = structured_checks(template_dir)
    failures.extend(f"structured_artifacts: {error}" for error in errors)
    ui = structured.pop("_ui")
    screenshots, errors = screenshot_checks(template_dir, ui)
    failures.extend(f"screenshots: {error}" for error in errors)
    replay, errors = replay_check(template_record, replay_record)
    failures.extend(f"comprehensive_replay: {error}" for error in errors)
    checks = {
        **script_results,
        "structured_artifacts": structured,
        "screenshots": screenshots,
        "floxml_well_formed": {
            "status": "passed" if not floxml_errors else "failed",
            "file_count": len(floxml_paths),
            "errors": floxml_errors,
        },
        "interactive_baseline_replay": baseline_check,
        "comprehensive_replay": replay,
        "single_variable_variations": variation_check,
    }
    return {
        "schema_version": "2.0",
        "template_id": template_dir.name,
        "software_version": "2504",
        "validated_at": validated_at,
        "status": "passed" if not failures else "failed",
        "checks": checks,
        "failures": failures,
    }, failures
