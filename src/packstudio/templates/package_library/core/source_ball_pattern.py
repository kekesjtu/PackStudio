"""Resolve PACK row counts and explicit X/Y ball coordinates without name guessing."""

import re

from packstudio.templates.package_library.core.array_solder_style import center_bounds, is_in_bounds
from packstudio.templates.package_library.core.parameters import BgaConfiguration


def source_bga_pattern(
    raw: dict,
    defaults: dict,
    ball_map_symbol: str | None,
) -> tuple[dict | None, list[str]]:
    if "bga.rows" not in defaults:
        return None, []
    configuration = BgaConfiguration().model_dump(mode="json")
    notes = []
    if raw.get("depop_center") == "CHECKED":
        configuration.update(
            solder_removal_enabled=True,
            removal_rows=raw["ME"] - raw["MEp"],
            removal_columns=raw["MD"] - raw["MDp"],
        )
    if raw.get("central_balls") == "CHECKED":
        configuration.update(
            center_solder_enabled=True,
            center_solder_rows=raw["MEc"],
            center_solder_columns=raw["MDc"],
        )
    for enabled, row, column in (
        ("solder_removal_enabled", "removal_rows", "removal_columns"),
        ("center_solder_enabled", "center_solder_rows", "center_solder_columns"),
    ):
        if configuration[enabled] and (
            (raw["ME"] - configuration[row]) % 2 or (raw["MD"] - configuration[column]) % 2
        ):
            configuration["allow_asymmetric_regions"] = True
            notes.append(
                "源区域与全阵列奇偶不同，按负轴方向取整定位，区域中心偏移半个节距；"
                "尚未完成原生 PACK 位置对照。"
            )
    ball_map = raw.get(ball_map_symbol) if ball_map_symbol else None
    if isinstance(ball_map, str) and ball_map.strip():
        coordinates = _parse_ball_coordinates(ball_map, raw["MD"], raw["ME"])
        configuration.update(
            solder_removal_enabled=True,
            removal_rows=0,
            removal_columns=0,
            center_solder_enabled=False,
            allow_asymmetric_regions=False,
            omitted_cells=[
                {"row": row, "column": column}
                for row in range(raw["ME"])
                for column in range(raw["MD"])
                if (column, row) not in coordinates
            ],
        )
        notes.append(
            "采用源 balls 逐球坐标列表；X 对应列、Y 对应行。去球区行列为 0，仅应用显式去球单元。"
        )
    return configuration, notes


def _parse_ball_coordinates(value: str, columns: int, rows: int) -> set[tuple[int, int]]:
    tokens = value.split(":")
    if not all(re.fullmatch(r"\d+x\d+", token) for token in tokens):
        raise ValueError("invalid PACK ball coordinate list")
    coordinates = [tuple(map(int, token.split("x"))) for token in tokens]
    if len(set(coordinates)) != len(coordinates):
        raise ValueError("duplicate PACK ball coordinates")
    if any(column >= columns or row >= rows for column, row in coordinates):
        raise ValueError("PACK ball coordinate lies outside the source array")
    return set(coordinates)


def source_ball_count(raw: dict, bga: dict) -> int:
    center = center_bounds(
        raw["ME"], raw["MD"], bga["center_solder_rows"], bga["center_solder_columns"]
    )
    removal = center_bounds(raw["ME"], raw["MD"], bga["removal_rows"], bga["removal_columns"])
    omitted = {(cell["row"], cell["column"]) for cell in bga["omitted_cells"]}
    return sum(
        (row, column) not in omitted
        and (
            bga["center_solder_enabled"]
            and is_in_bounds(row, column, center)
            or not bga["solder_removal_enabled"]
            or not is_in_bounds(row, column, removal)
        )
        for row in range(raw["ME"])
        for column in range(raw["MD"])
    )
