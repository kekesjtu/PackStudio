"""Map supported wizard inputs to explicit paths in the complete native catalog."""

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
        if isinstance(native, bool):
            values[key] = native
        elif "value" in native:
            value = native["value"]
            values[key] = (
                value != "ignored"
                if key == "vias.enabled" and isinstance(value, str)
                else "bare_die"
                if key == "cover.type" and value == "bareDie"
                else value
            )
        elif native["status"] == "not_applicable":
            inactive[key] = "/".join(path)
            if key == "leads.count_y":
                values[key] = 0
        else:
            raise ValueError(f"native value unavailable for {record['id']}/{key}: {native}")
    notes = []
    if inactive:
        notes.append(
            "PACK 未启用的参数："
            + ", ".join(sorted(inactive))
            + "；仅保留编辑初值，不计入当前模型。"
        )
    if record["id"] == "QFN_3X3_6":
        notes.append("two-sided QFN：Y 侧无引脚，未使用的节距仅保留编辑初值。")
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
            "inactive_editor_defaults": inactive,
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
