"""Copy screenshots from the current reference tree into staged output."""

import shutil
from pathlib import Path


def preserve_screenshots(source: Path, destination: Path, templates):
    records = []
    for family in sorted(templates):
        directory = source / "template" / family / "screenshots"
        if not directory.is_dir():
            continue
        for image in sorted(directory.rglob("*")):
            if not image.is_file() or image.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
                continue
            if not image.resolve().is_relative_to(source.resolve()):
                raise ValueError("screenshot path escapes reference root")
            relative = image.relative_to(source)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(image, target)
            records.append({"path": relative.as_posix()})
    return records
