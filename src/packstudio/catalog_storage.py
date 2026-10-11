"""Load immutable catalog entries and verify their indexed content hashes."""

import hashlib
from copy import deepcopy
from functools import cache

from packstudio.default_parameters import library_directory, read_defaults


@cache
def _verified_entry(relative: str, schema: str, digest: str) -> dict:
    root = library_directory().resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("catalog path must stay within the default library")
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(f"catalog content hash mismatch: {relative}")
    return read_defaults(relative, schema)


def read_catalog_entry(relative: str, schema: str, digest: str) -> dict:
    return deepcopy(_verified_entry(relative, schema, digest))
