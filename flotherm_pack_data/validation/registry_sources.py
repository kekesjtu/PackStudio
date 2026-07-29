"""Authoritative evidence sources for the PACK property registry."""

from __future__ import annotations

import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

AUTHENTIC_RECORDING_GLOBS = (
    "templates/*/logs/*.xml",
    "templates/*/baseline/script.xml",
    "validation/recorded_*.xml",
)


def binary_tokens(dlls: list[Path], strings_exe: Path) -> set[str]:
    tokens: set[str] = set()
    for dll in dlls:
        result = subprocess.run(
            [str(strings_exe), "-a", "-n", "4", str(dll)],
            check=True,
            capture_output=True,
            text=True,
            errors="ignore",
        )
        tokens.update(line.strip() for line in result.stdout.splitlines())
    return tokens


def recording_paths(data_root: Path) -> list[Path]:
    paths = {path for pattern in AUTHENTIC_RECORDING_GLOBS for path in data_root.glob(pattern)}
    return sorted(paths)


def recorded_commands(
    data_root: Path,
) -> tuple[dict[str, set[str]], dict[tuple[str, str], set[str]]]:
    starters: dict[str, set[str]] = defaultdict(set)
    modified: dict[tuple[str, str], set[str]] = defaultdict(set)
    for path in recording_paths(data_root):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        if root.tag != "flopack_xml_log_file":
            continue
        for command in root:
            if command.tag == "new_package":
                for value in command.findall("new_value"):
                    starters[value.attrib["property_name"]].add(value.attrib["new_value"])
            elif command.tag == "modify_component":
                key = (command.attrib["name"], command.attrib["property_name"])
                modified[key].add(command.attrib["new_value"])
    return starters, modified
