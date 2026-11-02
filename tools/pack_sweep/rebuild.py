"""Batch native replay, resumable validation and verified reference publication."""

import json
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

from tools.floscript.runner import replay
from tools.pack_sweep.artifacts import dump, write_indexes, write_point
from tools.pack_sweep.cases.attachments import cases as attachment_cases
from tools.pack_sweep.cases.metal_depth import cases as metal_cases
from tools.pack_sweep.catalog import Point, initial_points
from tools.pack_sweep.publish import publish
from tools.pack_sweep.screenshots import preserve_screenshots
from tools.pack_sweep.validate import validate_point, validate_tree


def dependent_points(stage, work, templates):
    baselines = work / "baselines"
    baselines.mkdir(exist_ok=True)
    attachment_families = {"chip_array", "cbga_fc", "pbga_fc"}
    # The attachment factory also defines PBGA FC core via-list cases.
    selected = attachment_families & templates
    if selected:
        for family in attachment_families:
            source = stage / "template" / family / (family + "-baseline") / "model.des"
            if family in selected:
                shutil.copy2(source, baselines / (family + "-baseline.des"))
        rows = attachment_cases(baselines, work / "attachment-inputs", families=selected)
    else:
        rows = []
    if "pbga_wb" in templates:
        rows += metal_cases(
            stage / "template/pbga_wb/wb-four-layer/model.des", work / "metal-inputs"
        )
    return [
        Point(
            row["request"]["template_id"],
            row["id"],
            row["commands"],
            row["request"],
            input_des=Path(ET.fromstring(row["commands"][0]).get("filename")),
        )
        for row in rows
    ]


def reusable(point, directory, installation):
    if not directory.exists():
        return False
    existing = json.loads((directory / "case.json").read_text(encoding="utf-8"))
    if (existing["template"], existing["id"]) != (point.template, point.id):
        raise ValueError(f"staged point identity differs: {point.key}")
    report = validate_point(directory, installation)
    dump(directory / "verification.json", report)
    return True


def execute_points(points, stage, work, installation, batch_size, timeout):
    pending = [p for p in points if not reusable(p, stage / "template" / p.key, installation)]
    runs = work / "runs"
    runs.mkdir(exist_ok=True)
    for start in range(0, len(pending), batch_size):
        batch = pending[start : start + batch_size]
        number = len(list(runs.iterdir())) + 1
        runtime = runs / f"batch-{number:04d}"
        cases = [{"id": f"p{i:06d}", "commands": p.commands} for i, p in enumerate(batch)]
        print(f"Native batch {number}: {len(batch)} points ({start}/{len(pending)})", flush=True)
        run = replay(installation, cases, runtime, timeout=timeout)
        if run["status"] != "success":
            raise RuntimeError(f"native batch failed: {runtime}: {run['errors']}")
        for point, case in zip(batch, cases, strict=True):
            destination = stage / "template" / point.key
            write_point(point, destination, runtime, case["id"], run, installation)
            try:
                report = validate_point(destination, installation)
            except Exception as error:
                raise ValueError(f"validation failed: {point.key}: {error}") from error
            dump(destination / "verification.json", report)
        print(f"Validated {start + len(batch)}/{len(pending)} pending points", flush=True)


def rebuild(output, work, installation, templates=None, batch_size=64, timeout=180):
    if batch_size < 1:
        raise ValueError("batch size must be positive")
    output, work = output.resolve(), work.resolve()
    if output.is_relative_to(work) or work.is_relative_to(output):
        raise ValueError("output and work directories must be separate")
    work.mkdir(parents=True, exist_ok=True)
    if (work / "previous-data").exists():
        raise FileExistsError("publication completed; use a new work directory")
    stage = work / "staging"
    if stage.is_symlink() or stage.is_junction():
        raise ValueError("staging directory cannot redirect to another directory")
    stage.mkdir(exist_ok=True)
    points = initial_points()
    families = {p.template for p in points}
    if templates:
        if set(templates) - families:
            raise ValueError("unknown template selection")
        points = [p for p in points if p.template in templates]
        families = set(templates)
    configuration = {
        "output": str(output),
        "installation": str(installation),
        "templates": sorted(families),
    }
    state = work / "rebuild.json"
    if state.exists() and json.loads(state.read_text(encoding="utf-8")) != configuration:
        raise ValueError("rebuild configuration changed; use a new work directory")
    dump(state, configuration)
    execute_points(points, stage, work, installation, batch_size, timeout)
    extra = dependent_points(stage, work, families)
    if len({p.key for p in points + extra}) != len(points + extra):
        raise ValueError("duplicate dependent point")
    execute_points(extra, stage, work, installation, batch_size, timeout)
    points += extra
    screenshots = preserve_screenshots(output, stage, families)
    dump(stage / "screenshots.json", screenshots)
    write_indexes(stage, points)
    report = validate_tree(stage, installation)
    dump(stage / "verification.json", report)
    backup = publish(stage, output, work)
    return {
        "status": report["status"],
        "point_count": len(points),
        "screenshots": len(screenshots),
        "output": str(output),
        "backup": str(backup) if backup else None,
    }
