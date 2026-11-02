"""Publish staged output with rollback and retain the previous directory."""

from pathlib import Path


def publish(stage: Path, output: Path, work: Path) -> Path | None:
    stage, output, work = stage.resolve(), output.resolve(), work.resolve()
    if not stage.is_relative_to(work) or output.is_relative_to(work) or work.is_relative_to(output):
        raise ValueError("staging, output and work directories must be separate")
    previous = work / "previous-data"
    if previous.exists():
        raise FileExistsError("previous publication requires a new work directory")
    had_output = output.exists()
    if had_output:
        output.rename(previous)
    try:
        stage.rename(output)
    except OSError:
        if had_output:
            previous.rename(output)
        raise
    return previous if had_output else None
