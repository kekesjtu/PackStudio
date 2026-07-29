"""Reusable semantic FloXML comparison primitives."""

from __future__ import annotations

import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

NUMBER_PATTERN = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def normalized_text(value: str | None) -> str:
    text = (value or "").strip()
    if NUMBER_PATTERN.fullmatch(text):
        return format(float(text), ".12g")
    return text


def equivalent(left: str, right: str) -> bool:
    if left == right:
        return True
    if NUMBER_PATTERN.fullmatch(left) and NUMBER_PATTERN.fullmatch(right):
        return math.isclose(float(left), float(right), rel_tol=1e-12, abs_tol=1e-15)
    return False


def direct_name(element: ET.Element) -> str | None:
    child = element.find("name")
    return child.text.strip() if child is not None and child.text else None


def flatten_leaves(root: ET.Element) -> dict[str, str]:
    leaves: dict[str, str] = {}

    def visit(element: ET.Element, path: str) -> None:
        for attribute, value in sorted(element.attrib.items()):
            leaves[f"{path}/@{attribute}"] = value
        children = list(element)
        if not children:
            leaves[path] = (element.text or "").strip()
            return
        occurrences: Counter[str] = Counter()
        for child in children:
            name = direct_name(child)
            base = f"{child.tag}[name={name}]" if name else child.tag
            occurrences[base] += 1
            suffix = f"#{occurrences[base]}" if occurrences[base] > 1 else ""
            visit(child, f"{path}/{base}{suffix}")

    visit(root, root.tag)
    return leaves


def material_map(root: ET.Element) -> dict[str, dict[str, str]]:
    materials: dict[str, dict[str, str]] = {}
    parent = root.find("./attributes/materials")
    if parent is None:
        return materials
    for material in parent:
        name = direct_name(material)
        if name:
            properties = {
                child.tag: normalized_text(child.text) for child in material if child.tag != "name"
            }
            materials[name] = {"type": material.tag, **properties}
    return materials


def canonical_fingerprint(element: ET.Element) -> str:
    def convert(item: ET.Element) -> Any:
        return [
            item.tag,
            sorted(item.attrib.items()),
            normalized_text(item.text),
            [convert(child) for child in item],
        ]

    payload = json.dumps(convert(element), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def entity_map(root: ET.Element) -> dict[str, list[str]]:
    entities: dict[str, list[str]] = defaultdict(list)

    def visit(element: ET.Element, inside_attributes: bool = False) -> None:
        nested_attributes = inside_attributes or element.tag == "attributes"
        name = direct_name(element)
        if name and not nested_attributes and element is not root:
            entities[f"{element.tag}:{name}"].append(canonical_fingerprint(element))
        for child in element:
            visit(child, nested_attributes)

    visit(root)
    return dict(entities)


def map_diff(baseline: dict[str, Any], variation: dict[str, Any]) -> dict[str, Any]:
    baseline_keys = set(baseline)
    variation_keys = set(variation)
    changed = sorted(
        key for key in baseline_keys & variation_keys if baseline[key] != variation[key]
    )
    return {
        "added": sorted(variation_keys - baseline_keys),
        "removed": sorted(baseline_keys - variation_keys),
        "changed": [
            {"name": key, "before": baseline[key], "after": variation[key]} for key in changed
        ],
    }


def analyze(baseline_path: Path, variation_path: Path) -> dict[str, Any]:
    baseline_root = ET.parse(baseline_path).getroot()
    variation_root = ET.parse(variation_path).getroot()
    baseline_leaves = flatten_leaves(baseline_root)
    variation_leaves = flatten_leaves(variation_root)
    shared_paths = set(baseline_leaves) & set(variation_leaves)
    changed_values = [
        {
            "path": path,
            "before": baseline_leaves[path],
            "after": variation_leaves[path],
        }
        for path in sorted(shared_paths)
        if not equivalent(baseline_leaves[path], variation_leaves[path])
    ]
    added_paths = sorted(set(variation_leaves) - set(baseline_leaves))
    removed_paths = sorted(set(baseline_leaves) - set(variation_leaves))
    materials = map_diff(material_map(baseline_root), material_map(variation_root))
    entities = map_diff(entity_map(baseline_root), entity_map(variation_root))
    semantic_change = any(
        (
            changed_values,
            added_paths,
            removed_paths,
            materials["added"],
            materials["removed"],
            materials["changed"],
            entities["added"],
            entities["removed"],
            entities["changed"],
        )
    )
    return {
        "schema_version": "2.0",
        "comparison": {
            "baseline": baseline_path.as_posix(),
            "variation": variation_path.as_posix(),
            "baseline_bytes": baseline_path.stat().st_size,
            "variation_bytes": variation_path.stat().st_size,
            "baseline_sha256": sha256(baseline_path),
            "variation_sha256": sha256(variation_path),
        },
        "semantic_change": semantic_change,
        "summary": {
            "changed_value_count": len(changed_values),
            "added_leaf_count": len(added_paths),
            "removed_leaf_count": len(removed_paths),
        },
        "materials": materials,
        "entities": entities,
        "changed_values": changed_values[:40],
        "added_leaf_paths": added_paths[:40],
        "removed_leaf_paths": removed_paths[:40],
        "numeric_formatting_differences_ignored": True,
    }


def summarize_map(diff: dict[str, Any]) -> dict[str, Any]:
    return {
        "added_count": len(diff["added"]),
        "removed_count": len(diff["removed"]),
        "changed_count": len(diff["changed"]),
        "added": diff["added"][:20],
        "removed": diff["removed"][:20],
        "changed": [item["name"] for item in diff["changed"][:20]],
    }
