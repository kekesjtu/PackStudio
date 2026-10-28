"""Reference-tool contracts independent of a licensed PACK process."""

import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

from tools.pack_sweep.archive import archive_tree, digest
from tools.pack_sweep.catalog import Point, fidelity_points, initial_points
from tools.pack_sweep.publish import publish
from tools.pack_sweep.rebuild import reusable
from tools.pack_sweep.screenshots import preserve_screenshots, snapshot_record

ROOT = Path(__file__).parents[2]


def test_fidelity_factory_preserves_independent_capture_requests():
    expected = {}
    for name in ("target-pack-fidelity", "remaining-pack-fidelity"):
        with ZipFile(ROOT / "docs/validation" / name / "evidence.zip") as archive:
            expected.update(
                {
                    row["id"]: row["request"]
                    for row in json.loads(archive.read("cases.json"))
                    if not row["commands"][0].startswith("<load_des")
                }
            )
    actual = {point.id: point.request for point in fidelity_points()}
    assert actual == expected
    points = initial_points()
    assert len({point.key for point in points}) == len(points)
    assert {point.template for point in points} == {
        "bare_die",
        "chip_array",
        "cbga_fc",
        "pbga_fc",
        "pbga_wb",
        "pqfp",
        "qfn",
        "sop",
    }
    assert all(
        ET.fromstring(command).tag not in {"save_des", "export_floxml", "quit"}
        for point in points
        for command in point.commands
    )


@pytest.mark.parametrize("identifier", ["../escape", "/absolute", "..", "a/b", "a\\b"])
def test_point_rejects_directory_traversal(identifier):
    with pytest.raises(ValueError, match="unsafe"):
        Point("bare_die", identifier, [])


def source_tree(tmp_path):
    source = tmp_path / "flotherm_pack_data"
    image = source / "templates/chip_array/screenshots/step.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"screenshot content")
    (source / "hidden.log").write_bytes(b"native evidence")
    (source / "empty").mkdir()
    snapshot = tmp_path / "archive/full.zip"
    record = archive_tree(source, snapshot)
    return source, snapshot, record


def test_snapshot_contains_every_file_and_screenshots_are_preserved(tmp_path):
    source, snapshot, record = source_tree(tmp_path)
    assert record["verified"] and record["file_count"] == 2
    assert snapshot_record(snapshot) == record
    with ZipFile(snapshot) as archive:
        for name, item in record["files"].items():
            assert archive.read(name) == (source.parent / name).read_bytes()
            assert item["sha256"] == digest(source.parent / name)
        assert "flotherm_pack_data/empty/" in archive.namelist()
    stage = tmp_path / "stage"
    images = preserve_screenshots(snapshot, stage)
    assert len(images) == 1
    assert (stage / images[0]["path"]).read_bytes() == b"screenshot content"
    snapshot.write_bytes(b"damaged archive")
    with pytest.raises(ValueError, match="digest"):
        snapshot_record(snapshot)


def test_publish_rejects_source_changes_after_snapshot(tmp_path):
    source, _, record = source_tree(tmp_path)
    work = tmp_path / "work"
    stage = work / "stage"
    stage.mkdir(parents=True)
    (stage / "new.xml").write_text("new", encoding="utf-8")
    (source / "hidden.log").write_text("edited after snapshot", encoding="utf-8")
    with pytest.raises(ValueError, match="source changed"):
        publish(stage, source, work, record)
    assert stage.exists() and source.exists()
    assert not (work / "previous-data").exists()


def test_publish_requires_matching_snapshot_and_replaces_only_the_tree(tmp_path):
    source, snapshot, record = source_tree(tmp_path)
    work = tmp_path / "work"
    stage = work / "stage"
    stage.mkdir(parents=True)
    (stage / "new.xml").write_bytes(b"new native output")
    with pytest.raises(ValueError, match="snapshot"):
        publish(stage, source, work, None)
    publish(stage, source, work, record)
    assert list(source.iterdir()) == [source / "new.xml"]
    assert snapshot.exists() and not (work / "previous-data").exists()


def test_resume_refuses_changed_inputs_before_reusing_native_output(tmp_path):
    point = Point("bare_die", "baseline", ["<new_package/>"])
    (tmp_path / "case.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="input changed"):
        reusable(point, tmp_path, ROOT)


def test_publish_rolls_back_if_staging_cannot_be_moved(tmp_path, monkeypatch):
    source, _, record = source_tree(tmp_path)
    work = tmp_path / "work"
    stage = work / "stage"
    stage.mkdir(parents=True)
    rename = Path.rename

    def fail_stage(path, target):
        if path == stage:
            raise OSError("simulated publication failure")
        return rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_stage)
    with pytest.raises(OSError, match="simulated"):
        publish(stage, source, work, record)
    assert (source / "hidden.log").read_bytes() == b"native evidence"
    assert stage.exists() and not (work / "previous-data").exists()


def test_failed_native_process_cannot_produce_reference_points(tmp_path, monkeypatch):
    from tools.pack_sweep.rebuild import execute_points

    monkeypatch.setattr(
        "tools.pack_sweep.rebuild.replay",
        lambda *a, **k: {"status": "failed", "exit_code": 1, "errors": ["native failure"]},
    )
    point = Point("bare_die", "baseline", ["<new_package/>"])
    with pytest.raises(RuntimeError, match="native failure"):
        execute_points([point], tmp_path / "stage", tmp_path, ROOT, 1, 60)
    assert not (tmp_path / "stage").exists()
