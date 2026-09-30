"""ECXML 1.0 geometry/material exchange; native simulation controls stay in comments."""

import json
from collections import defaultdict
from math import isfinite

from lxml import etree

from packstudio.domain.model import PackageModel


def export_ecxml(model: PackageModel) -> bytes:
    """Export SI coordinates without PTA slicing or overlapping source geometry."""
    root = etree.Element("neutralXML")
    _text(root, "name", model.name)
    # The published schema admits only these two producer values. This selects
    # the FloTHERM compatibility profile; the comment records the real author.
    _text(root, "producer", "FloTHERM")
    materials = etree.SubElement(root, "materials")
    for material in model.materials:
        element = etree.SubElement(materials, "material")
        # IDs, rather than display names, keep custom material references unique.
        _text(element, "name", material.id)
        _number(element, "density", material.density)
        _number(element, "specific_heat", material.specific_heat)
        # Material has no emissivity field; radiation remains disabled (0).
        _number(element, "surfaceEmissivity", 0)
        conductivity = etree.SubElement(element, "thermalConductivity")
        tensor = material.conductivity
        if tensor.x == tensor.y == tensor.z:
            _number(etree.SubElement(conductivity, "isotropic"), "conductivity", tensor.x)
        else:
            _vector(etree.SubElement(conductivity, "orthotropic"), tensor.model_dump())

    power_by_block: dict[str, float] = defaultdict(float)
    for source in model.heat_sources:
        power_by_block[source.block_id] += source.power_w
    groups_by_parent = defaultdict(list)
    blocks_by_parent = defaultdict(list)
    for group in model.groups:
        groups_by_parent[group.parent_id].append(group)
    for block in model.blocks:
        blocks_by_parent[block.parent_group_id].append(block)

    def append_groups(parent: etree._Element, parent_id: str | None) -> None:
        for group in groups_by_parent[parent_id]:
            assembly = etree.SubElement(parent, "assembly")
            _text(assembly, "name", group.id)
            _text(assembly, "active", "true")
            geometry = etree.SubElement(assembly, "geometry")
            for block in blocks_by_parent[group.id]:
                element = etree.SubElement(geometry, "solid3dBlock")
                _text(element, "name", block.id)
                _text(element, "active", "true")
                _vector(etree.SubElement(element, "location"), block.origin.model_dump(), 0.001)
                _vector(etree.SubElement(element, "size"), block.size.model_dump(), 0.001)
                _text(element, "material", block.material_id)
                _number(element, "powerDissipation", power_by_block[block.id])
            append_groups(geometry, group.id)

    append_groups(etree.SubElement(root, "geometry"), None)
    # ECXML has no portable face boundary or mesh-control syntax. Preserve the
    # source values for audit without inventing elements that importers ignore.
    audit = {
        "exporter": "PackStudio",
        "profile": "ECXML 1.0 / FloTHERM",
        "units": "m, W, kg/m3, J/(kg*K), W/(m*K)",
        "limitations": "Face boundaries and mesh controls are not applied by ECXML importers.",
        "boundaries": [item.model_dump(mode="json") for item in model.boundaries],
        "metadata": model.metadata,
        "material_names": {item.id: item.name for item in model.materials},
        "group_names": {item.id: item.name for item in model.groups},
        "block_names": {item.id: item.name for item in model.blocks},
    }
    # XML comments forbid '--'; JSON unicode escapes preserve the original text.
    comment = json.dumps(audit, ensure_ascii=True, allow_nan=False).replace("--", r"\u002d\u002d")
    root.append(etree.Comment(f"PackStudio export metadata: {comment}"))
    return etree.tostring(root, encoding="utf-8", xml_declaration=True, pretty_print=True)


def _text(parent: etree._Element, name: str, value: str) -> None:
    etree.SubElement(parent, name).text = value


def _number(parent: etree._Element, name: str, value: float) -> None:
    if not isfinite(value):
        raise ValueError(f"ECXML {name} requires a finite number")
    _text(parent, name, format(value, ".17g"))


def _vector(parent: etree._Element, values: dict[str, float], scale: float = 1) -> None:
    for axis in ("x", "y", "z"):
        _number(parent, axis, values[axis] * scale)
