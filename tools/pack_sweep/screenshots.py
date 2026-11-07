"""Copy screenshots from the current reference tree into staged output."""

import json
import shutil
from pathlib import Path


def preserve_screenshots(source: Path, destination: Path, packages):
    records = []
    entries = json.loads((source / "screenshots.json").read_text(encoding="utf-8"))
    for record in entries:
        relative = Path(record["path"])
        parts = relative.parts
        if len(parts) < 4 or parts[0] != "packages" or parts[2] != "screenshots":
            raise ValueError(f"invalid screenshot path: {relative}")
        if parts[1] not in packages:
            continue
        image = (source / relative).resolve()
        if not image.is_relative_to(source.resolve() / "packages" / parts[1] / "screenshots"):
            raise ValueError("screenshot path escapes its package")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image, target)
        records.append(record)
    return records
