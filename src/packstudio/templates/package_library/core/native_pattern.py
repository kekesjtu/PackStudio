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
    if depop["depopulatedCenter"]["value"]:
        if cells:
            raw["balls"] = ":".join(f"{c['column']}x{c['row']}" for c in cells)
        else:
            raw.update(
                depop_center="CHECKED",
                MDp=depop["numberFullyPopulatedRowsMDp"]["value"],
                MEp=depop["numberFullyPopulatedRowsMEp"]["value"],
            )
    elif cells:
        notes.append("PACK 保留逐球坐标，但 depopulatedCenter 未启用；默认采用完整阵列。")
    if center["centralBalls"]["value"]:
        raw.update(
            central_balls="CHECKED",
            MDc=center["numberCentralRowsMDp"]["value"],
            MEc=center["numberCentralRowsMEp"]["value"],
        )
    pattern, converted_notes = source_bga_pattern(raw, values, "balls")
    return pattern, notes + converted_notes
