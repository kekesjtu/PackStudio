"""Replay the indexed native inputs and publish the verified package library."""

import json
import shutil
from xml.etree import ElementTree as ET

from tools.floscript.runner import replay
from tools.pack_sweep.artifacts import dump, point_payload, write_indexes, write_point
from tools.pack_sweep.catalog import Point
from tools.pack_sweep.publish import publish
from tools.pack_sweep.screenshots import preserve_screenshots
from tools.pack_sweep.validate import validate_point, validate_tree


def indexed_samples(source, packages):
    index = json.loads((source / "index.json").read_text(encoding="utf-8"))
    families = set(index["packages"])
    if packages:
        if set(packages) - families:
            raise ValueError("unknown package selection")
        families = set(packages)
    samples = []
    for relative in index["points"]:
        parts = relative.split("/")
        if (
            len(parts) < 4 or parts[0] != "packages" or parts[1] not in index["packages"]
            or any(part in {"", ".", ".."} for part in parts)
        ):
            raise ValueError(f"invalid sample path: {relative}")
        if parts[1] not in families:
            continue
        directory = (source / relative).resolve()
        if not directory.is_relative_to(source / "packages" / parts[1]):
            raise ValueError(f"sample path escapes package: {relative}")
        case = json.loads((directory / "case.json").read_text(encoding="utf-8"))
        if case["id"] != relative or case["template"] != parts[1]:
            raise ValueError(f"indexed sample identity differs: {relative}")
        commands = []
        input_des = None
        for command in case["commands"]:
            node = ET.fromstring(command)
            if node.tag == "load_des":
                if node.get("filename") != "input.des":
                    raise ValueError(f"DES input must be local to its sample: {relative}")
                input_des = (directory / "input.des").resolve(strict=True)
                if input_des.parent != directory:
                    raise ValueError(f"DES input escapes sample: {relative}")
                node.set("filename", str(input_des))
            commands.append(ET.tostring(node, encoding="unicode"))
        samples.append((relative, Point(
            case["template"], "native", commands, case["request"], case["origin"],
            case["metadata"], input_des,
        )))
    if not samples or len({relative for relative, _ in samples}) != len(samples):
        raise ValueError("expected a nonempty index with unique sample paths")
    return samples, families


def reusable(relative, point, directory, installation):
    if not directory.exists():
        return False
    existing = json.loads((directory / "case.json").read_text(encoding="utf-8"))
    if existing != point_payload(point, relative):
        raise ValueError(f"staged sample input differs: {relative}")
    report = validate_point(directory, installation)
    dump(directory / "verification.json", report)
    return True


def execute_points(samples, stage, work, installation, batch_size, timeout):
    pending = [
        (relative, point) for relative, point in samples
        if not reusable(relative, point, stage / relative, installation)
    ]
    runs = work / "runs"
    runs.mkdir(exist_ok=True)
    for start in range(0, len(pending), batch_size):
        batch = pending[start : start + batch_size]
        number = len(list(runs.iterdir())) + 1
        runtime = runs / f"batch-{number:04d}"
        cases = [
            {"id": f"p{i:06d}", "commands": point.commands}
            for i, (_, point) in enumerate(batch)
        ]
        print(f"Native batch {number}: {len(batch)} points ({start}/{len(pending)})", flush=True)
        run = replay(installation, cases, runtime, timeout=timeout)
        if run["status"] != "success":
            raise RuntimeError(f"native batch failed: {runtime}: {run['errors']}")
        for (relative, point), case in zip(batch, cases, strict=True):
            destination = stage / relative
            write_point(
                point, destination, runtime, case["id"], run, installation, sample_id=relative,
            )
            report = validate_point(destination, installation)
            dump(destination / "verification.json", report)
        print(f"Validated {start + len(batch)}/{len(pending)} pending points", flush=True)


def rebuild(source, output, work, installation, packages=None, batch_size=64, timeout=180):
    if batch_size < 1:
        raise ValueError("batch size must be positive")
    source, output, work = source.resolve(), output.resolve(), work.resolve()
    if output.is_relative_to(work) or work.is_relative_to(output):
        raise ValueError("output and work directories must be separate")
    samples, families = indexed_samples(source, packages)
    work.mkdir(parents=True, exist_ok=True)
    if (work / "previous-data").exists():
        raise FileExistsError("publication completed; use a new work directory")
    stage = work / "staging"
    if stage.is_symlink() or stage.is_junction():
        raise ValueError("staging directory cannot redirect to another directory")
    stage.mkdir(exist_ok=True)
    configuration = {
        "source": str(source), "output": str(output),
        "installation": str(installation), "packages": sorted(families),
    }
    state = work / "rebuild.json"
    if state.exists() and json.loads(state.read_text(encoding="utf-8")) != configuration:
        raise ValueError("rebuild configuration changed; use a new work directory")
    dump(state, configuration)
    execute_points(samples, stage, work, installation, batch_size, timeout)
    screenshots = preserve_screenshots(source, stage, families)
    dump(stage / "screenshots.json", screenshots)
    shutil.copy2(source / "README.md", stage / "README.md")
    write_indexes(stage, samples)
    report = validate_tree(stage, installation)
    dump(stage / "verification.json", report)
    if report["status"] != "passed":
        raise ValueError(f"parameter coverage is incomplete: {stage / 'verification.json'}")
    backup = publish(stage, output, work)
    return {
        "status": report["status"], "point_count": len(samples),
        "screenshots": len(screenshots), "output": str(output),
        "backup": str(backup) if backup else None,
    }
