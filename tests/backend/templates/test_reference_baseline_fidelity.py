from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

import pytest

from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.catalog import (
    default_request,
    definition,
)
from packstudio.templates.package_library.core.materials import production_materials

REFERENCE_ROOT = Path(__file__).parents[3] / "flotherm_pack_data" / "templates"
TEMPLATE_IDS = (
    "flip_chip_cbga",
    "flip_chip_pbga",
    "wirebond_pbga",
    "fbga_fsbga",
    "qfn",
    "qfp_family",
    "soic_family",
    "bare_die",
)

type GeometryRecord = tuple[float, float, float, float, float, float]
type MaterialFingerprint = tuple[float, float, float, float, float]
type MaterialRecord = tuple[GeometryRecord, MaterialFingerprint]


def _record(origin: tuple[float, ...], size: tuple[float, ...]) -> GeometryRecord:
    return tuple(round(value, 9) for value in (*origin, *size))


def _reference_geometry(template_id: str) -> Counter[GeometryRecord]:
    root = ElementTree.parse(REFERENCE_ROOT / template_id / "baseline" / "model.xml").getroot()
    records: Counter[GeometryRecord] = Counter()
    for cuboid in root.findall(".//cuboid"):
        position = cuboid.find("position")
        size = cuboid.find("size")
        assert position is not None and size is not None
        origin = tuple(float(position.findtext(axis, "0")) * 1000 for axis in "xyz")
        dimensions = tuple(float(size.findtext(axis, "0")) * 1000 for axis in "xyz")
        records[_record(origin, dimensions)] += 1
    return records


def _native_geometry(template_id: str) -> Counter[GeometryRecord]:
    item = definition(template_id)
    request = default_request(template_id)
    built = item.builder(item.validate_request(request), request)
    records = Counter(_record(draft.origin, draft.size) for draft in built.drafts)
    for block in built.blocks:
        if block.structure_type is StructureType.STATIC_AIR:
            continue
        origin = (block.origin.x, block.origin.y, block.origin.z)
        size = (block.size.x, block.size.y, block.size.z)
        records[_record(origin, size)] += 1
    return records


def _fingerprint(
    conductivity: tuple[float, float, float],
    density: float,
    specific_heat: float,
) -> MaterialFingerprint:
    values = (*conductivity, density, specific_heat)
    return tuple(round(value, 7) for value in values)


def _reference_materials(root: ElementTree.Element) -> dict[str, MaterialFingerprint]:
    result: dict[str, MaterialFingerprint] = {}
    parent = root.find("./attributes/materials")
    assert parent is not None
    for material in parent:
        name = material.findtext("name")
        assert name is not None
        scalar = material.findtext("conductivity")
        if scalar is not None:
            conductivity = (float(scalar),) * 3
        elif material.findtext("in_plane_conductivity") is not None:
            in_plane = float(material.findtext("in_plane_conductivity", "0"))
            conductivity = (
                in_plane,
                in_plane,
                float(material.findtext("normal_conductivity", "0")),
            )
        else:
            conductivity = tuple(
                float(material.findtext(f"{axis}_conductivity", "0")) for axis in "xyz"
            )
        result[name] = _fingerprint(
            conductivity,
            float(material.findtext("density", "0")),
            float(material.findtext("specific_heat", "0")),
        )
    return result


def _native_material_records(
    template_id: str,
) -> tuple[Counter[MaterialRecord], set[GeometryRecord]]:
    item = definition(template_id)
    request = default_request(template_id)
    built = item.builder(item.validate_request(request), request)
    materials = production_materials() | {material.id: material for material in built.materials}
    records: Counter[MaterialRecord] = Counter()
    special_geometry: set[GeometryRecord] = set()
    objects = [*built.drafts, *built.blocks]
    for block in objects:
        if block.structure_type is StructureType.STATIC_AIR:
            continue
        if hasattr(block.origin, "x"):
            origin = (block.origin.x, block.origin.y, block.origin.z)
            size = (block.size.x, block.size.y, block.size.z)
        else:
            origin = block.origin
            size = block.size
        geometry = _record(origin, size)
        if block.structure_type is StructureType.FLIP_CHIP_BUMP:
            special_geometry.add(geometry)
            continue
        material = materials[block.material_id]
        fingerprint = _fingerprint(
            (
                material.conductivity.x,
                material.conductivity.y,
                material.conductivity.z,
            ),
            material.density,
            material.specific_heat,
        )
        records[(geometry, fingerprint)] += 1
    return records, special_geometry


def _reference_material_records(
    template_id: str,
    excluded_geometry: set[GeometryRecord],
) -> Counter[MaterialRecord]:
    root = ElementTree.parse(REFERENCE_ROOT / template_id / "baseline" / "model.xml").getroot()
    materials = _reference_materials(root)
    records: Counter[MaterialRecord] = Counter()
    for cuboid in root.findall(".//cuboid"):
        position = cuboid.find("position")
        size = cuboid.find("size")
        assert position is not None and size is not None
        geometry = _record(
            tuple(float(position.findtext(axis, "0")) * 1000 for axis in "xyz"),
            tuple(float(size.findtext(axis, "0")) * 1000 for axis in "xyz"),
        )
        if geometry in excluded_geometry:
            continue
        material_name = cuboid.findtext("material")
        assert material_name is not None
        records[(geometry, materials[material_name])] += 1
    return records


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_handwritten_baseline_cuboids_match_reference_floxml(template_id: str) -> None:
    expected = _reference_geometry(template_id)
    actual = _native_geometry(template_id)

    assert actual == expected, {
        "missing": list((expected - actual).elements())[:12],
        "unexpected": list((actual - expected).elements())[:12],
        "expected_count": expected.total(),
        "actual_count": actual.total(),
    }


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_handwritten_baseline_material_properties_match_reference_floxml(
    template_id: str,
) -> None:
    actual, special_geometry = _native_material_records(template_id)
    expected = _reference_material_records(template_id, special_geometry)

    assert actual == expected, {
        "missing": list((expected - actual).elements())[:6],
        "unexpected": list((actual - expected).elements())[:6],
    }
