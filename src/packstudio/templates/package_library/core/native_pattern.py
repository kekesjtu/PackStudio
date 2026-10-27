"""Honor native branch switches before converting PACK ball layout inputs."""

from packstudio.templates.package_library.core.source_ball_pattern import source_bga_pattern


def native_bga_pattern(branch: dict, values: dict) -> tuple[dict | None, list[str]]:
    if "bga.rows" not in values:
        return None, []
    raw = {"ME": values["bga.rows"], "MD": values["bga.columns"]}
    groups = branch["groups"]
    depop = groups["solderBallDepopulation"]["properties"]
    center = groups["centralBalls"]["properties"]
    notes = []
    cells = depop["depopulationDialog"]["value"]["native_cell_list"]
    raw.update(
        MDp=depop["numberFullyPopulatedRowsMDp"].get("value"),
        MEp=depop["numberFullyPopulatedRowsMEp"].get("value"),
        MDc=center["numberCentralRowsMDp"].get("value"),
        MEc=center["numberCentralRowsMEp"].get("value"),
    )
    if depop["depopulatedCenter"]["value"]:
        if cells:
            raw["balls"] = ":".join(f"{c['column']}x{c['row']}" for c in cells)
        else:
            raw["depop_center"] = "CHECKED"
    elif cells:
        notes.append("PACK 保留逐球坐标，但 depopulatedCenter 未启用；默认采用完整阵列。")
    if center["centralBalls"]["value"]:
        raw["central_balls"] = "CHECKED"
    pattern, converted_notes = source_bga_pattern(raw, values, "balls")
    pattern.update(
        depopulated_center=depop["depopulatedCenter"]["value"] if cells else None,
        populated_rows=raw.get("MEp"),
        populated_columns=raw.get("MDp"),
        staggered=groups["solderBalls"]["properties"]["staggeredMatrix"]["value"],
        center_staggered=center["staggeredMatrix"]["value"],
    )
    return pattern, notes + converted_notes
