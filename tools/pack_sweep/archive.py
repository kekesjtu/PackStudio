"""Verified whole-directory snapshots before replacing local reference data."""

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def archive_tree(source: Path, destination: Path) -> dict:
    source, destination = source.resolve(strict=True), destination.resolve()
    if not source.is_dir() or destination.is_relative_to(source):
        raise ValueError("archive must be outside the source directory")
    manifest_path = destination.with_suffix(destination.suffix + ".manifest.json")
    if destination.exists() or manifest_path.exists():
        raise FileExistsError("snapshot destination already exists")
    entries = sorted(source.rglob("*"))
    if any(path.is_symlink() or path.is_junction() for path in entries):
        raise ValueError("reference snapshots require ordinary files and directories")
    destination.parent.mkdir(parents=True, exist_ok=True)
    records = {}
    with ZipFile(destination, "x", ZIP_DEFLATED, compresslevel=6) as archive:
        archive.mkdir(source.name + "/")
        for path in entries:
            name = source.name + "/" + path.relative_to(source).as_posix()
            if path.is_dir():
                archive.mkdir(name)
                continue
            records[name] = {"bytes": path.stat().st_size, "sha256": digest(path)}
            archive.write(path, name)
    with ZipFile(destination) as archive:
        for name, record in records.items():
            with archive.open(name) as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if actual != record["sha256"] or archive.getinfo(name).file_size != record["bytes"]:
                raise ValueError(f"snapshot verification failed: {name}")
    result = {
        "schema": "packstudio.reference-snapshot/v1",
        "source": str(source),
        "archive": str(destination),
        "archive_sha256": digest(destination),
        "file_count": len(records),
        "bytes": sum(r["bytes"] for r in records.values()),
        "verified": True,
        "files": records,
    }
    manifest_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result
