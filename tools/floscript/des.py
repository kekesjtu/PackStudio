"""Read and write the parameter member of a local PACK DES ZIP archive."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def read_des(path: Path) -> dict[str, str]:
    with ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".des")]
        if len(members) != 1:
            raise ValueError(f"expected one DES parameter member: {path}")
        return dict(
            line.split("|", 1)
            for line in archive.read(members[0]).decode("utf-8-sig").splitlines()
            if "|" in line
        )


def write_des(path: Path, values: dict[str, str]) -> None:
    """Write a parameter-only DES; attachments require an explicit caller policy."""
    for key, value in values.items():
        if not key or any(c in key for c in "|\r\n") or any(c in value for c in "\r\n"):
            raise ValueError("invalid DES parameter key or multiline value")
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr(path.name, "".join(f"{key}|{value}\n" for key, value in values.items()))
