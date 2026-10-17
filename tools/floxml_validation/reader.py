"""Strict SI FloXML reader; assembly translations are accumulated in millimetres."""

import json
from dataclasses import dataclass
from math import isfinite, prod
from pathlib import Path
from xml.etree import ElementTree as ET


@dataclass(frozen=True)
class Box:
    name: str
    origin: tuple[float, ...]
    size: tuple[float, ...]
    material: str
    path: str = ""
    role: str = "unknown"
    priority: int = 20
    identity: str = ""

    @property
    def volume(self):
        return prod(self.size)

    @property
    def high(self):
        return tuple(a + b for a, b in zip(self.origin, self.size, strict=True))


@dataclass
class Document:
    boxes: list[Box]
    materials: dict[str, tuple[float, ...]]
    sources: list[dict]
    temperature_materials: dict
    collapsed_solids: list[str]
    nonphysical_entities: list[dict]


def _number(value):
    result = float(value)
    if not isfinite(result):
        raise ValueError("nonfinite FloXML number")
    return result


def _vector(element, name, default=False):
    vector = element.find(name)
    if vector is None and default:
        return (0.0, 0.0, 0.0)
    if vector is None:
        raise ValueError(f"missing {name}")
    return tuple(_number(vector.findtext(axis)) * 1000 for axis in "xyz")


def read(path: Path) -> Document:
    root = ET.parse(path).getroot()
    if root.tag != "xml_case":
        raise ValueError("expected FloXML xml_case")
    materials, temperature = {}, {}
    for element in root.findall("attributes/materials/*"):
        if any("curve" in child.tag for child in element):
            raise ValueError("conductivity curves require an explicit evaluation policy")
        name = element.findtext("name")
        if name in materials:
            raise ValueError(f"duplicate material {name}")
        if element.tag in {"isotropic_material_att", "temperature_dependant_material_att"}:
            tensor = (_number(element.findtext("conductivity")),) * 3
        elif element.tag == "orthotropic_material_att":
            tensor = tuple(_number(element.findtext(f"{axis}_conductivity")) for axis in "xyz")
        elif element.tag == "biaxial_material_att":
            tensor = (_number(element.findtext("in_plane_conductivity")),) * 2 + (
                _number(element.findtext("normal_conductivity")),
            )
        else:
            raise ValueError(f"unsupported material {element.tag}")
        materials[name] = (
            *tensor,
            _number(element.findtext("density")),
            _number(element.findtext("specific_heat")),
        )
        if element.tag == "temperature_dependant_material_att":
            temperature[name] = {key: _number(element.findtext(key)) for key in ("coeff", "tref")}
    source_attributes = {}
    for element in root.findall("attributes/sources/source_att"):
        if element.findtext("type") != "total" or element.find("source_options") is not None:
            raise ValueError("unsupported non-total or multi-option source")
        source_attributes[element.findtext("name")] = _number(element.findtext("power"))
    boxes, sources, collapsed, nonphysical = [], [], [], []

    def visit(geometry, offset=(0.0, 0.0, 0.0), parent="", inherited=None):
        if geometry is None:
            return
        for element in geometry:
            if element.findtext("active", "true") == "false":
                continue
            if element.find("orientation") is not None:
                raise ValueError("orientation requires a reviewed tensor/coordinate transform")
            name = element.findtext("name", "")
            path = f"{parent}/{name}"
            position = _vector(element, "position", default=True)
            origin = tuple(a + b for a, b in zip(offset, position, strict=True))
            material = element.findtext("material", inherited)
            if element.tag == "assembly":
                if element.findtext("ignore", "false") == "true":
                    raise ValueError("ignored assembly semantics require review")
                visit(element.find("geometry"), origin, path, material)
            elif element.tag in {"cuboid", "source"}:
                if element.find("holes") is not None or element.find("occupancy") is not None:
                    raise ValueError(
                        "holes or source occupancy require an explicit geometry policy"
                    )
                if element.find("thermal") is not None:
                    raise ValueError("thermal attributes require a reviewed source/boundary policy")
                size = _vector(element, "size")
                if min(size) <= 0:
                    raise ValueError("nonpositive size")
                if element.tag == "source":
                    source_id = element.findtext("source")
                    sources.append(
                        {
                            "path": path,
                            "origin": origin,
                            "size": size,
                            "power_w": source_attributes[source_id],
                            "collapse": element.findtext("collapse/type"),
                            "collapse_direction": element.findtext("collapse/direction"),
                            "attachment_side": element.findtext("attachment_side"),
                        }
                    )
                    continue
                if material not in materials:
                    raise ValueError(f"unresolved material {material} at {path}")
                notes = element.findtext("notes", "")
                role = "unknown"
                if notes.startswith('{"name":'):
                    role = json.loads(notes).get("structure_type", "unknown")
                boxes.append(Box(name, origin, size, material, path, role))
                if element.find("collapse") is not None:
                    collapsed.append(path)
            elif element.tag in {"monitor_point", "region"}:
                if element.find("material") is not None or element.find("thermal") is not None:
                    raise ValueError("unexpected material or thermal attribute on control region")
                nonphysical.append({"type": element.tag, "path": path})
            else:
                raise ValueError(f"unsupported geometry {element.tag}")

    visit(root.find("geometry"))
    return Document(boxes, materials, sources, temperature, collapsed, nonphysical)
