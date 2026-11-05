"""Behavior of generated requests and failed native execution."""

from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

from tools.pack_sweep.archive import archive_tree
from tools.pack_sweep.catalog import Point, initial_points
from tools.pack_sweep.compare import compare_native
from tools.pack_sweep.publish import publish
from tools.pack_sweep.rebuild import execute_points
from tools.pack_sweep.screenshots import preserve_screenshots


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


def test_comparison_matches_product_physics_without_native_controls(monkeypatch):
    native = ET.fromstring("""<xml_case><attributes><materials>
      <temperature_dependant_material_att><name>native-silicon</name>
        <density>2330</density><specific_heat>700</specific_heat><conductivity>117.5</conductivity>
        <coeff>-0.42</coeff><tref>373.15</tref>
      </temperature_dependant_material_att></materials><sources><source_att>
        <name>heat</name><power>2</power></source_att></sources>
      <grid_constraints><grid_constraint_att><name>grid</name></grid_constraint_att></grid_constraints>
      </attributes><geometry><cuboid><name>die</name><material>native-silicon</material>
        <position><x>-0.001</x><y>-0.002</y><z>0</z></position>
        <size><x>0.002</x><y>0.004</y><z>0.0002</z></size></cuboid>
        <monitor_point><name>junction</name></monitor_point></geometry></xml_case>""")
    product = """<model version="1"><materials>
      <material id="m1" type="temperature_dependent"><density>2330</density>
        <specific_heat>700</specific_heat><conductivity x="117.5" y="117.5" z="117.5"/>
        <coefficient>-0.42</coefficient><reference_temperature>373.15</reference_temperature>
      </material></materials><sources><source block="b1" power="2"/></sources>
      <group><block id="b1" x="-0.001" y="-0.002" z="0" dx="0.002" dy="0.004" dz="0.0002"/>
        <material>m1</material></group></model>"""
    monkeypatch.setattr("tools.pack_sweep.compare.export_model", lambda request: product)
    result = compare_native(native, {"template_id": "bare_die"})
    assert result["blocks"] == 1
    assert result["geometry"] == result["materials"] == result["power"] == "passed"
    assert "auxiliary" not in result
    for old, new in [
        ('dx="0.002"', 'dx="0.003"'), ('power="2"', 'power="3"'), ('x="117.5"', 'x="120"'),
    ]:
        monkeypatch.setattr(
            "tools.pack_sweep.compare.export_model",
            lambda request, a=old, b=new: product.replace(a, b),
        )
        with pytest.raises(ValueError, match="differs|mismatch"):
            compare_native(native, {"template_id": "bare_die"})


@pytest.mark.parametrize("identifier", ["../escape", "/absolute", "..", "a/b", "a\\b"])
def test_point_rejects_directory_traversal(identifier):
    with pytest.raises(ValueError, match="unsafe"):
        Point("bare_die", identifier, [])


@pytest.mark.parametrize("exit_code", [0, 1])
def test_failed_native_process_cannot_produce_reference_points(tmp_path, monkeypatch, exit_code):
    monkeypatch.setattr(
        "tools.pack_sweep.rebuild.replay",
        lambda *a, **k: {
            "status": "failed", "exit_code": exit_code,
            "errors": ["invalid export_floxml output model.xml: Element invalid"],
        },
    )
    point = Point("bare_die", "baseline", ["<new_package/>"])
    with pytest.raises(RuntimeError, match="native batch failed"):
        execute_points([point], tmp_path / "stage", tmp_path, Path(__file__).parents[2], 1, 60)
    assert not (tmp_path / "stage").exists()


def test_archive_and_screenshot_copy_keep_directory_layout(tmp_path):
    source = tmp_path / "source"
    image = source / "template/bare_die/screenshots/page.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"image")
    (source / "empty").mkdir()
    archive = tmp_path / "backup.zip"
    archive_tree(source, archive)
    with ZipFile(archive) as container:
        assert "source/template/bare_die/screenshots/page.png" in container.namelist()
        assert "source/empty/" in container.namelist()
    target = tmp_path / "staging"
    records = preserve_screenshots(source, target, {"bare_die"})
    assert (target / records[0]["path"]).is_file()


def test_publish_retains_previous_output_and_rolls_back_on_failure(tmp_path, monkeypatch):
    work, output = tmp_path / "work", tmp_path / "output"
    stage = work / "stage"
    stage.mkdir(parents=True)
    output.mkdir()
    (output / "original.xml").touch()
    (stage / "new.xml").touch()
    rename = Path.rename

    def fail_stage(path, destination):
        if path == stage:
            raise OSError("publication failed")
        return rename(path, destination)

    monkeypatch.setattr(Path, "rename", fail_stage)
    with pytest.raises(OSError, match="publication failed"):
        publish(stage, output, work)
    assert (output / "original.xml").is_file() and stage.exists()
    monkeypatch.setattr(Path, "rename", rename)
    previous = publish(stage, output, work)
    assert (output / "new.xml").is_file()
    assert (previous / "original.xml").is_file()
