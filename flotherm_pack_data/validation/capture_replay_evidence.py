"""Capture final combined-suite evidence from the active PACK log."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from validation_common import read_json, write_json

EXPORT_MARKER = "<export_floxml "
ERROR_MARKER = '<message text="ERROR'
WARNING_MARKER = '<message text="WARNING'
TEMPLATE_PATTERN = re.compile(r"[\\/]templates[\\/]([^\\/]+)[\\/]")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def final_run_lines(log_path: Path, expected_exports: int) -> tuple[list[str], int]:
    lines = log_path.read_text(encoding="utf-8").splitlines()
    export_indexes = [index for index, line in enumerate(lines) if EXPORT_MARKER in line]
    if len(export_indexes) < expected_exports:
        raise ValueError(
            f"log has {len(export_indexes)} exports, expected at least {expected_exports}"
        )
    first_export = export_indexes[-expected_exports]
    start = first_export
    while start > 0 and "<new_package " not in lines[start]:
        start -= 1
    return lines[start:], start + 1


def template_export_counts(lines: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in lines:
        if EXPORT_MARKER not in line:
            continue
        match = TEMPLATE_PATTERN.search(line)
        if match:
            template_id = match.group(1)
            counts[template_id] = counts.get(template_id, 0) + 1
    return counts


def build_evidence(
    data_root: Path,
    log_path: Path,
    process_id: int | None,
    application_remained_open: bool,
) -> dict:
    coverage = read_json(data_root / "parameter_coverage.json")
    expected = coverage["expected_export_count"]
    lines, start_line = final_run_lines(log_path, expected)
    exports = sum(EXPORT_MARKER in line for line in lines)
    errors = sum(ERROR_MARKER in line for line in lines)
    warnings = sum(WARNING_MARKER in line for line in lines)
    counts = template_export_counts(lines)
    template_records = []
    for template in coverage["templates"]:
        template_id = template["template_id"]
        expected_template = template["expected_export_count"]
        actual = counts.get(template_id, 0)
        passed = actual == expected_template and errors == 0 and warnings == 0
        template_records.append(
            {
                "template_id": template_id,
                "suite": template["suite"],
                "status": "passed" if passed else "failed",
                "expected_export_count": expected_template,
                "successful_export_count": actual,
                "final_error_count": errors,
                "final_warning_count": warnings,
                "evidence": "final_combined_suite",
            }
        )
    suite = data_root / coverage["global_suite"]
    complete = (
        application_remained_open
        and exports == expected
        and errors == 0
        and warnings == 0
        and all(item["status"] == "passed" for item in template_records)
    )
    return {
        "schema_version": "2.0",
        "software_version": "2504",
        "captured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "complete" if complete else "failed",
        "application_remained_open": application_remained_open,
        "process_id": process_id,
        "execution": {
            "suite": coverage["global_suite"],
            "suite_sha256": sha256(suite),
            "log_file": str(log_path),
            "log_start_line": start_line,
            "log_end_line": start_line + len(lines) - 1,
            "expected_export_count": expected,
            "successful_export_count": exports,
            "error_count": errors,
            "warning_count": warnings,
        },
        "templates": template_records,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "data_root",
        nargs="?",
        type=Path,
        default=Path("flotherm_pack_data"),
    )
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--process-id", type=int)
    parser.add_argument("--application-remained-open", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evidence = build_evidence(
        args.data_root,
        args.log,
        args.process_id,
        args.application_remained_open,
    )
    write_json(args.data_root / "validation/replay_results.json", evidence)
    print(
        json.dumps(
            {
                "status": evidence["status"],
                **{
                    key: evidence["execution"][key]
                    for key in (
                        "expected_export_count",
                        "successful_export_count",
                        "error_count",
                        "warning_count",
                    )
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if evidence["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
