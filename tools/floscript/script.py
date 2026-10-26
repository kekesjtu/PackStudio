"""FloSCRIPT construction, schema validation and file path resolution."""

import re
from collections import OrderedDict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from lxml import etree

from tools.floscript.environment import INSTALLATION, paths


def validate(path: Path, installation: Path = INSTALLATION, *, floxml: bool = False) -> None:
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    schema_path = paths(installation)["floxml_schema" if floxml else "script_schema"]
    schema = etree.XMLSchema(etree.parse(str(schema_path), parser))
    schema.assertValid(etree.parse(str(path), parser))


def write_xml(root: ET.Element, path: Path) -> None:
    ET.indent(root, space="    ")
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def replay_script(cases: list[dict], directory: Path) -> ET.Element:
    root = ET.Element("flopack_xml_log_file", version="1.0")
    seen = set()
    if not cases:
        raise ValueError("replay requires at least one case")
    for case in cases:
        identifier = case["id"]
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*", identifier) or identifier in seen:
            raise ValueError(f"invalid or duplicate case ID: {identifier}")
        seen.add(identifier)
        root.extend(ET.fromstring(command) for command in case["commands"])
        ET.SubElement(root, "save_des", filename=str(directory / f"{identifier}.des"))
        ET.SubElement(root, "export_floxml", filename=str(directory / f"{identifier}.xml"))
    ET.SubElement(root, "quit")
    return root


def normalize(root: ET.Element, source: Path, directory: Path) -> ET.Element:
    """Resolve inputs beside the source script and outputs inside the new run."""
    if root.tag != "flopack_xml_log_file":
        raise ValueError("expected PACK flopack_xml_log_file")
    commands = list(root)
    if any(command.tag == "quit" for command in commands[:-1]):
        raise ValueError("quit must be the last command")
    if any(command.tag == "project_run_script" for command in commands):
        raise ValueError("nested scripts must be expanded before running and validating outputs")
    if not commands or commands[-1].tag != "quit":
        ET.SubElement(root, "quit")
    for command in root:
        if command.tag not in {"load_des", "save_des", "export_floxml"}:
            continue
        filename = command.get("filename")
        if not filename:
            raise ValueError(f"{command.tag} requires an explicit filename")
        path = Path(filename)
        if not path.is_absolute():
            path = (source.parent if command.tag == "load_des" else directory) / path
        path = path.resolve()
        if command.tag != "load_des" and not path.is_relative_to(directory):
            raise ValueError(f"output must be inside the run directory: {path}")
        command.set("filename", str(path))
    return root


def files(root: ET.Element, directory: Path) -> tuple[list[Path], list[tuple[str, Path]]]:
    inputs, outputs, seen, exports = [], [], set(), set()
    for command in root:
        if command.tag == "load_des":
            path = Path(command.attrib["filename"])
            # A DES saved earlier in this script is a generated intermediate.
            if path not in seen:
                if not path.is_file():
                    raise FileNotFoundError(f"DES input missing: {path}")
                inputs.append(path)
        elif command.tag in {"save_des", "export_floxml"}:
            path = Path(command.attrib["filename"])
            if not path.is_relative_to(directory):
                raise ValueError(f"output must be inside the run directory: {path}")
            if path in seen or path.exists():
                raise FileExistsError(f"duplicate or existing output: {path}")
            if (
                path == directory / "replay.xml"
                or path.name
                in {
                    "run.json",
                    "runtime.json",
                    "process.json",
                    "run_pack.ps1",
                    "stdout.txt",
                    "stderr.txt",
                    "launcher-stdout.txt",
                    "launcher-stderr.txt",
                }
                or path.relative_to(directory).parts[0]
                in {"config", "central", "user", "temp", "LogFiles"}
            ):
                raise ValueError(f"output conflicts with runtime files: {path}")
            seen.add(path)
            outputs.append((command.tag, path))
            if command.tag == "export_floxml":
                if path.stem in exports:
                    raise ValueError(f"export basenames must be unique: {path.stem}")
                exports.add(path.stem)
    if not exports:
        raise ValueError("script must contain export_floxml")
    return inputs, outputs


def scalar_text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return format(value, ".12g")
    return str(value)


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
