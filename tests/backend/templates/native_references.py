"""Read versioned native reference points without a local PACK installation."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[3] / "flotherm_pack_data"


def read_point(directory):
    return {
        **json.loads((directory / "case.json").read_text(encoding="utf-8")),
        "directory": directory,
    }


def product_cases():
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    return [
        case
        for relative in index["points"]
        if (case := read_point(ROOT / relative)).get("request") is not None
    ]


def verify_fingerprints(directory):
    run = json.loads((directory / "native_run.json").read_text(encoding="utf-8"))
    assert run["status"] == "success"
    assert run["checks"]["script_schema"] and run["checks"]["outputs"]
    for name, expected in run["files"].items():
        path = (directory / name).resolve()
        assert path.is_relative_to(directory.resolve())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path
    return run
