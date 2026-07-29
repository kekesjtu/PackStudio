"""Small helpers for deterministic FloSCRIPT sweep generation."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import OrderedDict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from flopack_registry_data import ENUM_VALUE_MAP


def baseline_definition(path: Path) -> tuple[str, OrderedDict[str, str]]:
    root = ET.parse(path).getroot()
    package = root.find("new_package")
    if package is None:
        raise ValueError(f"{path}: new_package is missing")
    values: OrderedDict[str, str] = OrderedDict()
    for item in package.findall("new_value"):
        values[item.attrib["property_name"]] = item.attrib["new_value"]
    return package.attrib["package_type"], values


def scalar_text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return format(value, ".12g")
    return str(value)


def internal_value(value: Any) -> Any:
    return ENUM_VALUE_MAP.get(value, value)


def numeric_values(default: int | float, integer: bool = False) -> list[int | float]:
    if integer:
        default = int(default)
        if default == 0:
            return [1, 2]
        return [max(1, default - 1), default + 1]
    value = float(default)
    if value == 0:
        return [1.0, 2.0]
    return [float(format(value * 0.9, ".12g")), float(format(value * 1.1, ".12g"))]


def slug(value: Any, limit: int = 42) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")
    return (text or "value")[:limit].rstrip("_")


def new_package_element(
    package_type: str,
    baseline_values: OrderedDict[str, str],
    changes: dict[str, Any] | None = None,
    remove: set[str] | None = None,
) -> ET.Element:
    values = OrderedDict(baseline_values)
    for prop in remove or set():
        values.pop(prop, None)
    for prop, value in (changes or {}).items():
        values[prop] = scalar_text(value)
    package = ET.Element("new_package", {"package_type": package_type})
    for prop, value in values.items():
        ET.SubElement(
            package,
            "new_value",
            {"new_value": value, "property_name": prop},
        )
    return package


def component_element(component: str, prop: str, value: Any) -> ET.Element:
    return ET.Element(
        "modify_component",
        {
            "name": component,
            "new_value": scalar_text(value),
            "property_name": prop,
        },
    )


def make_script(
    package_type: str,
    baseline_values: OrderedDict[str, str],
    export_path: Path,
    commands: Iterable[tuple[str, str, Any]] = (),
    starter_changes: dict[str, Any] | None = None,
    starter_remove: set[str] | None = None,
) -> ET.Element:
    root = ET.Element("flopack_xml_log_file", {"version": "1.0"})
    root.append(
        new_package_element(
            package_type,
            baseline_values,
            starter_changes,
            starter_remove,
        )
    )
    for component, prop, value in commands:
        root.append(component_element(component, prop, value))
    ET.SubElement(root, "export_floxml", {"filename": str(export_path)})
    return root


def write_xml(root: ET.Element, path: Path) -> None:
    ET.indent(root, space="    ")
    path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(root)
    tree.write(path, encoding="UTF-8", xml_declaration=True, short_empty_elements=True)


def combined_suite(script_paths: Iterable[Path], output: Path) -> int:
    root = ET.Element("flopack_xml_log_file", {"version": "1.0"})
    export_count = 0
    for path in script_paths:
        script_root = ET.parse(path).getroot()
        for command in script_root:
            root.append(command)
            export_count += command.tag == "export_floxml"
    write_xml(root, output)
    return export_count


def relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()
