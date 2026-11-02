"""Read the repository's versioned runtime data for research tools."""

import json
from copy import deepcopy
from functools import cache
from pathlib import Path
from typing import Any


def library_directory() -> Path:
    return Path(__file__).resolve().parents[2] / "runtime_data"


@cache
def _read(relative: str, schema_version: str) -> dict[str, Any]:
    directory = library_directory().resolve()
    path = (directory / relative).resolve()
    if not path.is_relative_to(directory):
        raise ValueError("runtime data path must stay within the library")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"cannot read runtime data file {path}: {error}") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != schema_version:
        raise ValueError(f"unsupported runtime data schema in {path}")
    return payload


def read_defaults(relative: str, schema_version: str) -> dict[str, Any]:
    # Requests must not share mutable lists or dictionaries through the file cache.
    return deepcopy(_read(relative, schema_version))


def read_default_value(relative: str, schema_version: str, *keys: str) -> Any:
    """Copy only the requested value, keeping the cached document private."""
    value = _read(relative, schema_version)
    for key in keys:
        value = value[key]
    return deepcopy(value)


def read_default_keys(relative: str, schema_version: str, *keys: str) -> tuple[str, ...]:
    value = _read(relative, schema_version)
    for key in keys:
        value = value[key]
    return tuple(value)
