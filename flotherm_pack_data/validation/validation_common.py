"""Shared helpers for validating the FloTHERM PACK reference dataset."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from lxml import etree


def relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def iter_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


def validate_floscript(path: Path, schema: etree.XMLSchema) -> None:
    schema.assertValid(etree.parse(str(path)))


def variation_directory(template_dir: Path, variation_id: str) -> Path:
    matches = list(template_dir.glob(f"xml_variations/*/{variation_id}"))
    if len(matches) != 1:
        raise FileNotFoundError(
            f"{template_dir.name}/{variation_id}: expected one directory, got {len(matches)}"
        )
    return matches[0]


def manifest_variations(
    template_dir: Path,
    template_record: dict[str, Any],
) -> Iterator[tuple[dict[str, Any], Path, dict[str, Any]]]:
    for target in template_record["coverage"]:
        for variation_id in target.get("variation_ids", []):
            directory = variation_directory(template_dir, variation_id)
            yield target, directory, read_json(directory / "config.json")


def script_check(
    paths: list[Path],
    schema: etree.XMLSchema,
    schema_path: Path,
    root: Path,
) -> tuple[dict[str, Any], list[str]]:
    errors = []
    for path in paths:
        try:
            validate_floscript(path, schema)
        except (OSError, etree.XMLSyntaxError, etree.DocumentInvalid) as exc:
            errors.append(f"{relative(path, root)}: {exc}")
    return (
        {
            "status": "passed" if not errors else "failed",
            "schema": str(schema_path),
            "files": [relative(path, root) for path in paths],
            "file_count": len(paths),
            "errors": errors,
        },
        errors,
    )


def replay_check(
    template_record: dict[str, Any],
    replay_record: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[str]]:
    errors = []
    if replay_record is None:
        errors.append("missing replay evidence")
        replay_record = {}
    if replay_record.get("status") != "passed":
        errors.append("replay status is not passed")
    expected = template_record["expected_export_count"]
    if replay_record.get("expected_export_count") != expected:
        errors.append("expected export count mismatch")
    if replay_record.get("successful_export_count") != expected:
        errors.append("successful export count mismatch")
    if replay_record.get("final_error_count") != 0:
        errors.append("final error count is not zero")
    if replay_record.get("final_warning_count") != 0:
        errors.append("final warning count is not zero")
    return {**replay_record, "errors": errors}, errors
