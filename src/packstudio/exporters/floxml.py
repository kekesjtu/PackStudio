"""FloTHERM FloXML cuboids, SI materials and uncollapsed volumetric sources."""

import json
from collections import defaultdict
from math import isfinite

from lxml import etree

from packstudio.domain.model import PackageModel


def export_floxml(model: PackageModel) -> bytes:
    """Preserve PackageModel partitions; do not reconstruct PACK overlaps."""
    root = etree.Element("xml_case")
    _text(root, "name", model.name)
    attributes = etree.SubElement(root, "attributes")
    materials = etree.SubElement(attributes, "materials")
    for material in model.materials:
        tensor = material.conductivity
        isotropic = tensor.x == tensor.y == tensor.z
        element = etree.SubElement(
            materials, "isotropic_material_att" if isotropic else "orthotropic_material_att"
        )
        _text(element, "name", material.id)
        _number(element, "density", material.density)
        _number(element, "specific_heat", material.specific_heat)
        if isotropic:
            _number(element, "conductivity", tensor.x)
        else:
            for axis in "xyz":
                _number(element, f"{axis}_conductivity", getattr(tensor, axis))
        _text(element, "notes", material.name)

    sources = etree.SubElement(attributes, "sources")
    power_by_block: dict[str, float] = defaultdict(float)
    for source in model.heat_sources:
        power_by_block[source.block_id] += source.power_w
    for block_id, power in power_by_block.items():
        element = etree.SubElement(sources, "source_att")
        _text(element, "name", f"power-{block_id}")
        _text(element, "type", "total")
        _number(element, "power", power)

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
            _vector(assembly, "position", {axis: 0 for axis in "xyz"})
            geometry = etree.SubElement(assembly, "geometry")
            for block in blocks_by_parent[group.id]:
                element = etree.SubElement(geometry, "cuboid")
                _text(element, "name", block.id)
                _vector(element, "size", block.size.model_dump(), 0.001)
                _vector(element, "position", block.origin.model_dump(), 0.001)
                _text(element, "material", block.material_id)
                _text(
                    element,
                    "notes",
                    json.dumps(
                        {
                            "name": block.name,
                            "structure_type": block.structure_type.value,
                            "metadata": block.metadata,
                        },
                        ensure_ascii=False,
                        allow_nan=False,
                    ),
                )
                if block.id in power_by_block:
                    # A source has no material or occupancy: it adds power, not mass.
                    # No collapse: the internal model specifies a volume source.
                    element = etree.SubElement(geometry, "source")
                    _text(element, "name", f"heat-{block.id}")
                    _vector(element, "size", block.size.model_dump(), 0.001)
                    _vector(element, "position", block.origin.model_dump(), 0.001)
                    _text(element, "source", f"power-{block.id}")
            append_groups(geometry, group.id)
            _text(assembly, "notes", group.name)

    append_groups(etree.SubElement(root, "geometry"), None)
    _text(
        root,
        "notes",
        json.dumps(
            {
                "exporter": "PackStudio",
                "profile": "FloXML / FloTHERM 2504",
                "units": "m, W, kg/m3, J/(kg*K), W/(m*K)",
                "limitations": "Face boundaries and mesh controls require target-software setup.",
                "boundaries": [item.model_dump(mode="json") for item in model.boundaries],
                "metadata": model.metadata,
            },
            ensure_ascii=False,
            allow_nan=False,
        ),
    )
    return etree.tostring(root, encoding="utf-8", xml_declaration=True, pretty_print=True)


def _text(parent: etree._Element, name: str, value: str) -> None:
    etree.SubElement(parent, name).text = value


def _number(parent: etree._Element, name: str, value: float) -> None:
    if not isfinite(value):
        raise ValueError(f"FloXML {name} requires a finite number")
    _text(parent, name, format(value, ".17g"))


def _vector(parent: etree._Element, name: str, values: dict, scale: float = 1) -> None:
    element = etree.SubElement(parent, name)
    for axis in "xyz":
        _number(element, axis, values[axis] * scale)
