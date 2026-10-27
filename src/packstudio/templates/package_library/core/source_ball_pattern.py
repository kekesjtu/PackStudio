"""Resolve PACK row counts and explicit X/Y ball coordinates without name guessing."""

import re

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
    configuration["solder_removal_enabled"] = raw.get("depop_center") == "CHECKED"
    configuration["center_solder_enabled"] = raw.get("central_balls") == "CHECKED"
    if raw.get("MEp") is not None and raw.get("MDp") is not None:
        configuration.update(
            removal_rows=raw["ME"] - raw["MEp"],
            removal_columns=raw["MD"] - raw["MDp"],
        )
    if raw.get("MEc") is not None and raw.get("MDc") is not None:
        configuration.update(
            center_solder_rows=raw["MEc"],
            center_solder_columns=raw["MDc"],
        )
    for enabled, row, column in (
        ("solder_removal_enabled", "removal_rows", "removal_columns"),
        ("center_solder_enabled", "center_solder_rows", "center_solder_columns"),
    ):
        if configuration[enabled] and (configuration[row] is None or configuration[column] is None):
            raise ValueError(f"native {enabled} requires both row and column counts")
        if configuration[enabled] and (
            (raw["ME"] - configuration[row]) % 2 or (raw["MD"] - configuration[column]) % 2
        ):
            configuration["allow_asymmetric_regions"] = True
            notes.append(
                "阵列与区域奇偶不同；外围满布行列按每侧向下取整，中央焊球按独立阵列居中。"
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
    from packstudio.templates.package_library.bga.native_solder import main_cells

    configuration = BgaConfiguration.model_validate(bga)
    count = len(main_cells(configuration, raw["ME"], raw["MD"]))
    if configuration.center_solder_enabled:
        center_count = configuration.center_solder_rows * configuration.center_solder_columns
        count += (center_count + 1) // 2 if configuration.center_staggered else center_count
    return count
