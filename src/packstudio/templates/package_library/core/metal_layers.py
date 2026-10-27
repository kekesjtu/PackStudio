"""Explicit PACK depth tables; lengths in mm and coverage in percent."""

import json
from math import isfinite

from packstudio.domain.enums import StructureType
from packstudio.templates.package_library.core.geometry import centered_draft
from packstudio.templates.package_library.core.mixtures import mix_material


def parse_layers(value):
    try:
        rows = json.loads(value)
    except (ValueError, TypeError) as exc:
        raise ValueError("金属层表必须是有效的 JSON 表格") from exc
    if not isinstance(rows, list) or len(rows) > 10:
        raise ValueError("金属层表最多包含 10 行")
    for row in rows:
        if not isinstance(row, dict) or set(row) - {"disconnect"} != {
            "depth",
            "thickness",
            "coverage",
        }:
            raise ValueError("金属层表每行需要 depth、thickness、coverage")
        if any(
            isinstance(v, bool) or not isinstance(v, int | float) or not isfinite(v)
            for k, v in row.items()
            if k != "disconnect"
        ):
            raise ValueError("金属层表需要有限数值")
        if "disconnect" in row and not isinstance(row["disconnect"], bool):
            raise ValueError("Disconnect to Via 必须是布尔值")
        if row["depth"] < 0 or row["thickness"] <= 0 or not 0 <= row["coverage"] <= 100:
            raise ValueError("金属层深度 ≥ 0、厚度 > 0、覆盖率范围为 0–100%")
    return rows


def append_metal_layers(
    drafts,
    materials,
    rows,
    length,
    width,
    substrate_top,
    metal,
    matrix,
    prefix="trace",
    skip_zero_depth=False,
):
    for index, row in enumerate(rows):
        if skip_zero_depth and row["depth"] == 0:
            continue
        identifier = f"{prefix}-{index}"
        equivalent = mix_material(
            metal.model_copy(update={"id": identifier, "name": identifier}),
            metal,
            matrix,
            row["coverage"] / 100,
            set("xyz"),
        )
        materials.append(equivalent)
        drafts.append(
            centered_draft(
                identifier,
                identifier,
                StructureType.TRACE,
                (length, width, row["thickness"]),
                substrate_top - row["depth"] - row["thickness"],
                equivalent.id,
                "group-traces",
                "Dielectric & traces",
            )
        )
