"""Preserve every screenshot from a verified snapshot with collision detection."""

import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

from tools.pack_sweep.archive import digest


def snapshot_record(path: Path):
    manifest = json.loads(
        path.with_suffix(path.suffix + ".manifest.json").read_text(encoding="utf-8")
    )
    if not manifest["verified"] or digest(path) != manifest["archive_sha256"]:
        raise ValueError("snapshot verification is missing or its digest differs")
    return manifest


def preserve_screenshots(snapshot, root, templates=None):
    records = []
    with ZipFile(snapshot) as archive:
        for name in archive.namelist():
            parts = PurePosixPath(name).parts
            if len(parts) < 4 or parts[1] not in {"templates", "template"}:
                continue
            if templates is not None and parts[2] not in templates:
                continue
            if PurePosixPath(name).suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
                continue
            if any(part in {"..", "."} or ":" in part or "\\" in part for part in parts):
                raise ValueError("unsafe screenshot archive member")
            relative = (
                Path(*parts[parts.index("screenshots") + 1 :])
                if "screenshots" in parts
                else (Path("reference-" + "-".join(parts[3:])))
            )
            destination = root / "template" / parts[2] / "screenshots" / relative
            content = archive.read(name)
            fingerprint = hashlib.sha256(content).hexdigest()
            if destination.exists() and digest(destination) != fingerprint:
                raise ValueError(f"screenshot name collision: {name}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            records.append(
                {
                    "source": name,
                    "path": destination.relative_to(root).as_posix(),
                    "sha256": fingerprint,
                }
            )
    return records
