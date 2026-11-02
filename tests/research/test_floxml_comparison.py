from dataclasses import replace
from pathlib import Path

import pytest

from tools.floxml_validation.compare import compare
from tools.floxml_validation.partition import overlap_volume, partition, totals
from tools.floxml_validation.reader import Box, Document, read

MATERIALS = {"a": (1.0, 2.0, 3.0, 1000.0, 500.0), "b": (5.0, 6.0, 7.0, 2000.0, 100.0)}


def test_overlap_is_clipped_and_analytic_mass_and_capacity_are_preserved():
    boxes = [
        Box("a", (0.0, 0.0, 0.0), (2.0, 2.0, 2.0), "a", priority=1),
        Box("b", (1.0, 1.0, 1.0), (2.0, 2.0, 2.0), "b", priority=2),
    ]
    physical = partition(boxes)
    assert sum(b.volume for b in physical) == pytest.approx(15.0)
    assert all(overlap_volume(a, b) == 0 for i, a in enumerate(physical) for b in physical[i + 1 :])
    summary = totals(physical, MATERIALS)
    assert summary["mass_kg"] == pytest.approx((8 * 1000 + 7 * 2000) * 1e-9)
    assert summary["heat_capacity_j_k"] == pytest.approx((8 * 1000 * 500 + 7 * 2000 * 100) * 1e-9)


def test_material_rename_and_block_split_do_not_create_false_physical_differences():
    native = Box("native", (0.0, 0.0, 0.0), (2.0, 2.0, 2.0), "a", role="die")
    pieces = [
        replace(native, name="one", size=(1.0, 2.0, 2.0), material="renamed"),
        replace(
            native, name="two", origin=(1.0, 0.0, 0.0), size=(1.0, 2.0, 2.0), material="renamed"
        ),
    ]
    doc = Document([native], MATERIALS, [], {}, [], [])
    exported = Document(pieces, {"renamed": MATERIALS["a"]}, [], {}, [], [])
    result = compare(doc, exported, [native], MATERIALS)
    assert result["normalized"]["differences"] == []
    assert result["normalized"]["shared_volume_mm3"] == 8
    exported.materials["renamed"] = MATERIALS["b"]
    changed = compare(doc, exported, [native], MATERIALS)
    assert changed["normalized"]["property_mismatch_volume_mm3"]["kx"] == 8
    exported.boxes = [replace(b, origin=(b.origin[0] + 1.0, 0.0, 0.0)) for b in pieces]
    changed = compare(doc, exported, [native], MATERIALS)
    assert changed["normalized"]["pack_only_volume_mm3"] == 4
    doc.sources = [{"power_w": 1.0}]
    exported.sources = [{"power_w": 2.0}]
    changed = compare(doc, exported, [native], MATERIALS)
    assert not changed["sources"]["total_power_equal"]
    assert changed["sources"]["total_power_difference_w"] == 1


def test_reader_accumulates_nested_translations_and_inherits_material(tmp_path: Path):
    path = tmp_path / "nested.xml"
    path.write_text(
        """<xml_case><name>test</name><attributes><materials>
    <orthotropic_material_att><name>a</name><density>1000</density><specific_heat>500</specific_heat>
    <x_conductivity>1</x_conductivity><y_conductivity>2</y_conductivity>
    <z_conductivity>3</z_conductivity></orthotropic_material_att></materials></attributes>
    <geometry><assembly><name>outer</name><material>a</material>
    <position><x>0.001</x><y>0</y><z>0.002</z></position><geometry>
    <assembly><name>inner</name><position><x>-0.002</x><y>0.003</y><z>0</z></position><geometry>
    <cuboid><name>c</name><position><x>0.004</x><y>0</y><z>0</z></position>
    <size><x>0.001</x><y>0.002</y><z>0.003</z></size></cuboid>
    </geometry></assembly></geometry></assembly></geometry></xml_case>""",
        encoding="utf-8",
    )
    doc = read(path)
    assert doc.boxes[0].origin == pytest.approx((3.0, 3.0, 2.0))
    assert doc.boxes[0].size == (1.0, 2.0, 3.0)
    assert doc.boxes[0].material == "a"
    path.write_text(path.read_text().replace("<name>c</name>", "<name>c</name><orientation/>"))
    with pytest.raises(ValueError, match="orientation"):
        read(path)
