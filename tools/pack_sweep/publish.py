"""Publish a rebuilt tree only after verifying the complete original snapshot."""

import shutil
from pathlib import Path

from tools.pack_sweep.archive import digest


def publish(stage: Path, output: Path, work: Path, snapshot: dict | None):
    stage, output, work = stage.resolve(), output.resolve(), work.resolve()
    if not stage.is_relative_to(work) or output.is_relative_to(work) or work.is_relative_to(output):
        raise ValueError("staging, output and work directories must be separate")
    previous = work / "previous-data"
    if previous.exists():
        raise FileExistsError("previous publication requires manual recovery")
    if output.exists():
        if snapshot is None or Path(snapshot["source"]).resolve() != output:
            raise ValueError("replacing references requires their own verified snapshot")
        current = {
            output.name + "/" + p.relative_to(output).as_posix(): p
            for p in output.rglob("*")
            if p.is_file()
        }
        if current.keys() != snapshot["files"].keys():
            raise ValueError("source file set changed after snapshot")
        for name, path in current.items():
            if digest(path) != snapshot["files"][name]["sha256"]:
                raise ValueError(f"source changed after snapshot: {path}")
        output.rename(previous)
    try:
        stage.rename(output)
    except OSError:
        if previous.exists():
            previous.rename(output)
        raise
    if previous.exists():
        if previous.resolve().parent != work:
            raise ValueError("previous data cleanup escapes task work directory")
        shutil.rmtree(previous)
