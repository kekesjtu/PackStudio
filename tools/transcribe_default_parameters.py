"""Transcribe an installation inventory into portable, lossless JSON preset families."""

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

NUMERIC = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?\Z")


def typed_value(raw: str) -> str | int | float | None:
    if raw == "":
        return None
    if not NUMERIC.fullmatch(raw):
        return raw
    return float(raw) if any(character in raw for character in ".eE") else int(raw)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def transcribe(snapshot: Path, output: Path) -> dict:
    inventory = json.loads(snapshot.read_text(encoding="utf-8"))
    families = defaultdict(list)
    for record in inventory["records"]:
        families[record["family"]].append(
            {
                "id": Path(record["path"]).stem,
                "source_path": record["path"],
                "source_sha256": record["sha256"],
                "raw_fields": record["fields"],
                "values": {key: typed_value(value) for key, value in record["fields"].items()},
            }
        )
    entries = []
    for family, records in sorted(families.items()):
        path = output / "flotherm" / f"{family}.json"
        write_json(
            path,
            {
                "schema_version": "packstudio.flotherm-presets/v1",
                "family": family,
                "records": records,
            },
        )
        entries.append(
            {
                "family": family,
                "file": path.relative_to(output).as_posix(),
                "count": len(records),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    manifest = {
        "schema_version": "packstudio.default-parameters/v1",
        "source_product": "Simcenter FloTHERM PACK 2504",
        "source_snapshot_sha256": hashlib.sha256(
            snapshot.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest(),
        "file_hash_convention": "SHA-256 of UTF-8 JSON files with LF line endings; "
        "DES source_sha256 remains the original vendor byte hash.",
        "record_count": sum(entry["count"] for entry in entries),
        "value_convention": (
            "Original PACK symbols; numbers parsed without unit conversion; "
            "empty = null; raw_fields retained verbatim."
        ),
        "families": entries,
    }
    write_json(output / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--output", type=Path, default=Path("default_parameters"))
    arguments = parser.parse_args()
    manifest = transcribe(arguments.snapshot, arguments.output)
    print(f"Transcribed {manifest['record_count']} presets in {len(manifest['families'])} families")


if __name__ == "__main__":
    main()
