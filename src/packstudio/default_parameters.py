"""Read the versioned default library in source, wheel and frozen installations."""

import json
import sys
import sysconfig
from copy import deepcopy
from functools import cache
from pathlib import Path
from typing import Any


def library_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "default_parameters"
    source_directory = Path(__file__).resolve().parents[2] / "default_parameters"
    if source_directory.is_dir():
        return source_directory
    return Path(sysconfig.get_path("data")) / "default_parameters"


@cache
def _read(relative: str, schema_version: str) -> dict[str, Any]:
    directory = library_directory().resolve()
    path = (directory / relative).resolve()
    if not path.is_relative_to(directory):
        raise ValueError("default parameter path must stay within the library")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"cannot read default parameter file {path}: {error}") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != schema_version:
        raise ValueError(f"unsupported default parameter schema in {path}")
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


def request_default(section: str, key: str) -> Any:
    return read_default_value("request.json", "packstudio.request-defaults/v1", section, key)
