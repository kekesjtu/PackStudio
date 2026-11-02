"""Create a plain ZIP backup of a reference directory."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def archive_tree(source: Path, destination: Path) -> dict:
    source, destination = source.resolve(strict=True), destination.resolve()
    if not source.is_dir() or destination.is_relative_to(source):
        raise ValueError("archive must be outside the source directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    count, size = 0, 0
    with ZipFile(destination, "x", ZIP_DEFLATED, compresslevel=6) as archive:
        archive.mkdir(source.name + "/")
        for path in sorted(source.rglob("*")):
            if path.is_symlink() or path.is_junction():
                raise ValueError("reference archives require ordinary files and directories")
            name = source.name + "/" + path.relative_to(source).as_posix()
            if path.is_dir():
                archive.mkdir(name)
            else:
                archive.write(path, name)
                count += 1
                size += path.stat().st_size
    return {"source": str(source), "archive": str(destination), "file_count": count, "bytes": size}
