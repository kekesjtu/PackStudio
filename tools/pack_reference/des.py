"""Read original vendor DES parameter text."""

from pathlib import Path


def source_record(path: Path, installation: Path) -> dict:
    raw = path.read_bytes()
    fields = {}
    for line in raw.decode("utf-8-sig").splitlines():
        if not line:
            continue
        key, delimiter, value = line.partition("|")
        if not delimiter or not key or key in fields:
            raise ValueError(f"malformed or duplicate DES key in {path}: {line}")
        fields[key] = value
    return {
        "id": path.stem,
        "source_path": path.relative_to(installation).as_posix(),
        "raw_fields": fields,
    }
