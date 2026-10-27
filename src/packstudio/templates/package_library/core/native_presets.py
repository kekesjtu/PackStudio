"""Map supported wizard inputs to explicit paths in the complete native catalog."""

import json
import re

from packstudio.preset_catalog import PresetCatalog
from packstudio.runtime_data import read_defaults
from packstudio.templates.package_library.core.materials import material_id_for_name
from packstudio.templates.package_library.core.native_pattern import native_bga_pattern
from packstudio.templates.package_library.core.source_ball_pattern import source_ball_count


def read_binding(template_id: str) -> dict | None:
    families = read_defaults("pack_bindings.json", "packstudio.pack-bindings/v1")["families"]
    if template_id == "bare_die":
        return None
    if template_id not in families:
        raise ValueError(f"missing native PACK binding for {template_id}")
    return families[template_id]


def at_path(record: dict, path: list[str]):
    node = record
    for part in path:
        node = node[part]
    return node


def native_value(key, value):
    if isinstance(value, list):
        return json.dumps(
            [
                {
                    "depth": row["depth_m"] * 1000,
                    "thickness": row["thickness_m"] * 1000,
                    "coverage": row["coverage_percent"],
                }
                for row in value
                if row.get("status") == "specified"
            ]
        )
    if key in {"vias.filled", "bond_wire.auto_count", "upper.filled", "lower.filled"}:
        return value == "yes"
    if key == "bumps.array_type":
        return {"regularArray": "regular", "nonRegularArray": "non_regular"}[value]
    if key == "vias.enabled" and isinstance(value, str):
        return value != "ignored"
    if key == "cover.type" and value == "bareDie":
        return "bare_die"
    return value


def expand_native_presets(template_id: str, field: dict, fields: list[dict]) -> dict:
    binding = read_binding(template_id)
    if binding is None:
        return field
    catalog = PresetCatalog()
    presets = [
        _adapt(catalog.read(identifier), binding, fields)
        for identifier in catalog.list_ids(binding["family"])
    ]
    if field["default"] not in {p["value"] for p in presets}:
        raise ValueError(f"default preset is absent from native catalog: {template_id}")
    return {
        **field,
        "presets": presets,
        "options": [p["value"] for p in presets],
        "option_labels": {p["value"]: p["label"] for p in presets},
    }


def _adapt(record: dict, binding: dict, fields: list[dict]) -> dict:
    branch = record["branches"][record["default_branch"]]
    values, inactive = {}, {}
    for key, path in binding["parameters"].items():
        native = at_path(branch, path)
        if isinstance(native, list):
            native = {"value": native}
        if isinstance(native, bool):
            values[key] = native
        elif "value" in native:
            values[key] = native_value(key, native["value"])
        elif native["status"] == "not_applicable":
            inactive[key] = "/".join(path)
            values[key] = None
        else:
            raise ValueError(f"native value unavailable for {record['id']}/{key}: {native}")
    notes = []
    if inactive:
        notes.append(
            "PACK 未启用的参数："
            + ", ".join(sorted(inactive))
            + "；原生未给定数值，保持空白，不计入当前模型。"
        )
    if record["id"] == "QFN_3X3_6":
        notes.append("two-sided QFN：Y 侧无引脚，未使用的行数与节距保持空白。")
    bga, pattern_notes = native_bga_pattern(branch, values)
    notes.extend(pattern_notes)
    if bga is not None:
        raw = {"ME": values["bga.rows"], "MD": values["bga.columns"]}
        count = source_ball_count(raw, bga)
        match = re.search(r"_(\d+)_", record["id"])
        if match and int(match[1]) != count:
            notes.append(f"名称球数 {match[1]} 与原生启用阵列球数 {count} 不一致；采用原生参数。")
    assignments = {
        group: material_id_for_name(at_path(branch, path)["value"])
        for group, path in binding["materials"].items()
        if "value" in at_path(branch, path)
    }
    return {
        "value": record["id"],
        "label": record["id"],
        "values": values,
        "bga": bga,
        "material_assignments": assignments,
        "metadata": {
            "preset_source_path": record["source"]["path"],
            "preset_source_sha256": record["source"]["sha256"],
            "preset_geometry_status": "native-defaults-adapted",
            "reference_geometry_status": "supported-parameters-with-family-equivalent-geometry",
            "preset_notes": " ".join(notes),
        },
        "audit": {
            "native_parameter_paths": binding["parameters"],
            "inactive_parameters": inactive,
            "project_only_fields": [
                f["key"]
                for f in fields
                if f["control"] != "footprint" and f["key"] not in binding["parameters"]
            ],
            "native_material_names": {
                g: at_path(branch, p)["value"]
                for g, p in binding["materials"].items()
                if "value" in at_path(branch, p)
            },
        },
    }
