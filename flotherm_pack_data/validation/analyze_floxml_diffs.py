"""Analyze manifest-selected single-variable FloXML variations."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from floxml_diff_core import analyze, sha256, summarize_map


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def variation_directory(template_dir: Path, variation_id: str) -> Path:
    matches = list(template_dir.glob(f"xml_variations/*/{variation_id}"))
    if len(matches) != 1:
        raise FileNotFoundError(
            f"{template_dir.name}/{variation_id}: expected one directory, got {len(matches)}"
        )
    return matches[0]


def outcome_for(
    semantic_change: bool,
    expectation: dict[str, Any] | None,
) -> str:
    if semantic_change:
        return "semantic_change"
    if expectation and expectation.get("expectation") == "no_change_at_default_substate":
        return "accepted_no_floxml_effect"
    return "unexpected_no_change"


def selected_variations(
    templates_root: Path,
) -> Iterator[tuple[Path, Path, dict[str, Any]]]:
    coverage = read_json(templates_root.parent / "parameter_coverage.json")
    for template_record in coverage["templates"]:
        template_dir = templates_root / template_record["template_id"]
        for target in template_record["coverage"]:
            for variation_id in target.get("variation_ids", []):
                directory = variation_directory(template_dir, variation_id)
                config = read_json(directory / "config.json")
                if config["variation_id"] != variation_id:
                    raise ValueError(f"{variation_id}: config variation_id mismatch")
                yield template_dir, directory, config


def collect_results(templates_root: Path) -> list[dict[str, Any]]:
    results = []
    for template_dir, directory, config in selected_variations(templates_root):
        baseline = template_dir / config["comparison_baseline"]
        variation = directory / "model.xml"
        result = analyze(baseline, variation)
        expectation = config.get("floxml_effect_expectation")
        result.update(
            {
                "template_id": template_dir.name,
                "variation_id": config["variation_id"],
                "variation_kind": config["kind"],
                "comparison_baseline": config["comparison_baseline"],
                "outcome": outcome_for(result["semantic_change"], expectation),
                "floxml_effect_expectation": expectation,
            }
        )
        results.append(result)
    return results


def variation_record(result: dict[str, Any], template_dir: Path) -> dict[str, Any]:
    variation_id = result["variation_id"]
    directory = variation_directory(template_dir, variation_id)
    config_path = directory / "config.json"
    config = read_json(config_path)
    return {
        "variation_id": variation_id,
        "kind": config["kind"],
        "coverage_policy": config["coverage_policy"],
        "target": config["target"],
        "comparison_baseline": config["comparison_baseline"],
        "artifacts": {
            "config": relative(config_path, template_dir),
            "script": relative(directory / "script.xml", template_dir),
            "model": relative(directory / "model.xml", template_dir),
            "diff": relative(directory / "diff_xml.json", template_dir),
        },
        "semantic_change": result["semantic_change"],
        "outcome": result["outcome"],
        "floxml_effect_expectation": result["floxml_effect_expectation"],
        "summary": result["summary"],
        "materials": summarize_map(result["materials"]),
        "entities": summarize_map(result["entities"]),
    }


def write_artifacts(
    templates_root: Path,
    results: list[dict[str, Any]],
    generated_at: str,
) -> None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        template_dir = templates_root / result["template_id"]
        directory = variation_directory(template_dir, result["variation_id"])
        write_json(directory / "diff_xml.json", result)
        grouped[result["template_id"]].append(result)

    coverage = read_json(templates_root.parent / "parameter_coverage.json")
    expected = {item["template_id"]: item["variation_count"] for item in coverage["templates"]}
    for template_id, template_results in sorted(grouped.items()):
        template_dir = templates_root / template_id
        variations = [
            variation_record(result, template_dir)
            for result in sorted(template_results, key=lambda item: item["variation_id"])
        ]
        complete = len(variations) == expected[template_id] and all(
            item["outcome"] != "unexpected_no_change" for item in variations
        )
        comparison_baselines = sorted({item["comparison_baseline"] for item in variations})
        summary = {
            "schema_version": "2.0",
            "template_id": template_id,
            "generated_at": generated_at,
            "status": "complete" if complete else "failed",
            "baseline": {
                "model": "baseline/model.xml",
                "sha256": sha256(template_dir / "baseline/model.xml"),
            },
            "comparison_policy": {
                "manifest_selected_variations_only": True,
                "single_variable_relative_to_comparison_baseline": True,
                "conditional_targets_use_branch_baselines": True,
                "numeric_formatting_differences_ignored": True,
            },
            "comparison_baselines": comparison_baselines,
            "variation_count": len(variations),
            "expected_variation_count": expected[template_id],
            "semantic_change_count": sum(
                item["outcome"] == "semantic_change" for item in variations
            ),
            "accepted_no_floxml_effect_count": sum(
                item["outcome"] == "accepted_no_floxml_effect" for item in variations
            ),
            "unexpected_no_change_count": sum(
                item["outcome"] == "unexpected_no_change" for item in variations
            ),
            "variations": variations,
        }
        write_json(template_dir / "xml_variations.json", summary)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path("flotherm_pack_data/templates"),
    )
    parser.add_argument(
        "--write-artifacts",
        action="store_true",
        help="Write diff_xml.json and per-template xml_variations.json files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = collect_results(args.root)
    if args.write_artifacts:
        write_artifacts(
            args.root,
            results,
            datetime.now().astimezone().isoformat(timespec="seconds"),
        )
    summary = {
        "status": (
            "complete"
            if results and all(item["outcome"] != "unexpected_no_change" for item in results)
            else "failed"
        ),
        "variation_count": len(results),
        "semantic_change_count": sum(item["semantic_change"] for item in results),
        "accepted_no_floxml_effect_count": sum(
            item["outcome"] == "accepted_no_floxml_effect" for item in results
        ),
        "unexpected_no_change_count": sum(
            item["outcome"] == "unexpected_no_change" for item in results
        ),
        "template_count": len({item["template_id"] for item in results}),
        "manifest_driven": True,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
