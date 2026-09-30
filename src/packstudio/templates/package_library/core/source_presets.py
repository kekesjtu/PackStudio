"""Adapt the lossless PACK library using serialized, reviewable field mappings."""

import re

from packstudio.default_parameters import read_defaults
from packstudio.templates.package_library.core.source_ball_pattern import (
    source_ball_count,
    source_bga_pattern,
)


def expand_source_presets(template_id: str, field: dict, fields: list[dict]) -> dict:
    policy = read_defaults("source_adapters.json", "packstudio.source-adapters/v1")
    adapter = next(
        (
            dict(item, family=family)
            for family, item in policy["families"].items()
            if item["template_id"] == template_id
        ),
        None,
    )
    if adapter is None:
        if any("source" in preset for preset in field["presets"]):
            raise ValueError(f"missing source adapter for {template_id}")
        return field
    records = read_defaults(f"flotherm/{adapter['family']}.json", "packstudio.flotherm-presets/v1")[
        "records"
    ]
    if len({record["id"] for record in records}) != len(records):
        raise ValueError(f"duplicate PACK preset in {adapter['family']}")
    reviewed = {preset["value"]: preset for preset in field["presets"]}
    baseline_id = adapter["captured_baseline_id"]
    if baseline_id not in reviewed or baseline_id not in {record["id"] for record in records}:
        raise ValueError(f"missing captured baseline for {template_id}")
    defaults = {item["key"]: item["default"] for item in fields if item != field}
    presets = [
        _adapt(
            record, adapter, reviewed.get(record["id"]), defaults, record["id"] == baseline_id
        )
        for record in records
    ]
    return {
        **field,
        "presets": presets,
        "options": [preset["value"] for preset in presets],
        "option_labels": {preset["value"]: preset["label"] for preset in presets},
    }


def _adapt(
    record: dict, adapter: dict, reviewed: dict | None, defaults: dict, baseline: bool
) -> dict:
    raw = record["values"]
    values = dict(defaults)
    values.update((reviewed or {}).get("values", {}))
    inherited = set(defaults)
    mapped = {}
    for key, symbol in adapter["source_values"].items():
        value = raw.get(symbol)
        if value is None or isinstance(value, str) and not value.strip():
            continue
        if not isinstance(value, int | float) or isinstance(value, bool):
            raise ValueError(f"non-numeric PACK parameter {record['id']}/{symbol}")
        mapped[key] = value
        inherited.discard(key)
    bga, notes = source_bga_pattern(raw, values, adapter.get("ball_map_symbol"))
    for key, expression in adapter["derived_values"].items():
        operation = expression["operation"]
        if operation == "twice_sum":
            mapped[key] = 2 * sum(raw[symbol] for symbol in expression["symbols"])
        elif operation == "bga_count":
            mapped[key] = source_ball_count(raw, bga)
        else:
            raise ValueError(f"unknown source adapter operation {operation}")
        inherited.discard(key)
    differences = {}
    if baseline:
        # Captured default baselines also contain PACK's generated, implicit values.
        # Keep that evidence while continuing to resolve the explicitly linked Ld/Wd.
        linked = (reviewed or {}).get("source_values", {})
        differences = {
            key: {"source": value, "reviewed": values[key]}
            for key, value in mapped.items()
            if key not in linked and values[key] != value
        }
        mapped = {key: raw[symbol] for key, symbol in linked.items()}
    values.update(mapped)
    correction = adapter["record_overrides"].get(record["id"], {})
    values.update(correction.get("values", {}))
    if correction.get("note"):
        notes.append(correction["note"])
    match = re.search(r"_(\d+)_", record["id"])
    if bga is not None and match and int(match[1]) != source_ball_count(raw, bga):
        notes.append(
            f"名称球数 {match[1]} 与源阵列计算球数 {source_ball_count(raw, bga)} 不一致；"
            "采用源阵列，未猜测缺球位置。"
        )
    if differences:
        notes.append("保留已对照 PACK 导出的默认基线；源值差异列于参数审计。")
    return {
        "value": record["id"],
        "label": (reviewed or {}).get("label", record["id"]),
        "values": {
            key: values[key]
            for key in (
                set(adapter["source_values"])
                | set(adapter["derived_values"])
                | set((reviewed or {}).get("values", {}))
                | set(correction.get("values", {}))
            )
        },
        "bga": bga,
        "metadata": {
            "preset_source_path": record["source_path"],
            "preset_source_sha256": record["source_sha256"],
            "preset_geometry_status": "captured-default-baseline" if baseline else "source-adapted",
            "reference_geometry_status": "baseline-and-mapped-single-variable-transcription"
            if baseline
            else "source-adapted-with-family-equivalent-materials",
            "preset_notes": " ".join(notes),
        },
        "audit": {
            "mapped_values": mapped,
            "inherited_fields": sorted(inherited),
            "reviewed_baseline_values": differences,
            "source_material_names": {
                key: value
                for key, value in raw.items()
                if key.startswith("k") and isinstance(value, str)
            },
        },
    }
