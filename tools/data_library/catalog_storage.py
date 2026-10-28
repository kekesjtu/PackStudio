"""Load immutable catalog entries and verify their indexed content hashes."""

import hashlib
from copy import deepcopy
from functools import cache

import tools.data_library.runtime_data as library


@cache
def _verified_entry(directory: str, relative: str, schema: str, digest: str) -> dict:
    from pathlib import Path

    root = Path(directory)
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("catalog path must stay within the runtime data library")
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(f"catalog content hash mismatch: {relative}")
    return library.read_defaults(relative, schema)


def read_catalog_entry(relative: str, schema: str, digest: str) -> dict:
    return deepcopy(
        _verified_entry(str(library.library_directory().resolve()), relative, schema, digest)
    )
