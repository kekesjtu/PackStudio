"""Behavior of generated requests and failed native execution."""

from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from tools.pack_sweep.catalog import Point, initial_points
from tools.pack_sweep.rebuild import execute_points


def test_factory_emits_unique_points_and_flat_layout_overrides():
    points = initial_points()
    assert len({point.key for point in points}) == len(points)
    assert {point.template for point in points} == {
        "bare_die", "chip_array", "cbga_fc", "pbga_fc", "pbga_wb", "pqfp", "qfn", "sop"
    }
    for point in points:
        assert all(
            ET.fromstring(command).tag not in {"save_des", "export_floxml", "quit"}
            for command in point.commands
        )
        if point.request:
            assert "bga" not in point.request
            assert all(
                key.startswith(point.template + ".")
                for key in point.request.get("overrides", {})
            )


@pytest.mark.parametrize("identifier", ["../escape", "/absolute", "..", "a/b", "a\\b"])
def test_point_rejects_directory_traversal(identifier):
    with pytest.raises(ValueError, match="unsafe"):
        Point("bare_die", identifier, [])


def test_failed_native_process_cannot_produce_reference_points(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "tools.pack_sweep.rebuild.replay",
        lambda *a, **k: {"status": "failed", "exit_code": 1, "errors": ["native failure"]},
    )
    point = Point("bare_die", "baseline", ["<new_package/>"])
    with pytest.raises(RuntimeError, match="native failure"):
        execute_points([point], tmp_path / "stage", tmp_path, Path(__file__).parents[2], 1, 60)
    assert not (tmp_path / "stage").exists()
