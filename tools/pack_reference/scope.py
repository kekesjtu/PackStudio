"""Reviewed scope rules for the offline PACK option inventory."""

FIXED = {
    "outlineType": "《封装外形与芯片类型范围》：只提供 Standard Outline",
    "dieType": "《封装外形与芯片类型范围》：只提供 Actual Die",
}

BGA = {
    "depopulatedCenter": "bga.solder_removal_enabled",
    "numberFullyPopulatedRowsMDp": "bga.removal_columns",
    "numberFullyPopulatedRowsMEp": "bga.removal_rows",
    "centralBalls": "bga.center_solder_enabled",
    "numberCentralRowsMDp": "bga.center_solder_columns",
    "numberCentralRowsMEp": "bga.center_solder_rows",
    "modelSolderBallArrayAs": "bga.representation",
}

BARE = {
    "packagePower": "die.power",
    "dieLengthLd": "die.length",
    "dieWidthWd": "die.width",
    "dieThicknessTd": "die.thickness",
    "flippedDie": "die.flipped",
    "bumpedDie": "bumps.enabled",
    "numberOfSolderBalls": "bumps.total",
    "ballDiameterb": "bumps.diameter",
    "ballHeight": "bumps.height",
    "solderConductivity": "material.group-bump-solder",
    "underfillConductivity": "material.group-underfill",
}

STEP_ALIASES = {
    "die_flag_and_solder_mask": "die_flag_solder_mask",
    "die_flag_and_tie_bars": "die_flag_tie_bars",
    "lead_and_solder_interconnect": "lead_solder_interconnect",
    "lead_frame": "leadframe",
    "thermal_land_and_solder": "thermal_land_solder",
}


def decision(template, entry):
    """Return a scope classification before testing ordinary property mappings."""
    location, prop = entry["ui_location"], entry["property_name"]
    label = entry["label"]
    if location.startswith("drop_in_slug") or prop == "includeSlug":
        return "gap", "G04", "独立 slug、支脚与粘接配置缺失；plate 不是该结构"
    if "stiffener" in (prop or "").lower():
        return "gap", "G05", "顶盖 stiffener 分支缺失"
    if location in {"core_vias", "upper_built_up_region", "lower_built_up_region"}:
        return "gap", "C01", "显式基板分支未实现；不属于已确认的功能取舍"
    if template == "pbga_fc" and location == "metal_layers":
        return "gap", "C01", "未开放显式金属层栈；不属于已确认的功能取舍"
    if prop in {"nonUniformDieHeat", "nonUniformDieHeatDialog"}:
        return "explicit_tradeoff", None, "《仅支持均匀芯片热源》：八类模板不实现非均匀芯片热源"
    if location == "die" and label == "Click To Edit":
        return "explicit_tradeoff", None, "《仅支持均匀芯片热源》：不实现非均匀热源编辑器"
    if prop in {"userDefinedLeadframeCoverage", "leadframeCoveragePercentage"}:
        return "gap", "G03", "自定义覆盖率入口未实现；不属于已确认的功能取舍"
    if template == "chip_array":
        if prop == "filledVias":
            return "gap", "G07", "读取预设 filledVias，但没有编辑入口"
        if prop in {"numberBondWiresEqualsSolderBalls", "bondWireModeling"}:
            return "gap", "G08", "键合线数量关系和 Include/Ignore 未开放"
        if location == "metal_layers" and prop != "substrateLayer":
            return "gap", "G02", "金属选材、覆盖率和顶层开孔未开放"
    if template == "pbga_wb":
        if prop == "coveragePercentageCf" or location == "metal_layers":
            return "gap", "G02", "金属层与承载台覆盖率仅消费预设，不能编辑"
        if prop == "viaDepopulation":
            return "adapted", None, "当前实现使用共享区域及显式矩阵去孔 request.vias"
    if template == "qfn" and prop == "modelViasAs":
        return "gap", None, "当前启用后仅离散表达；其他表达未实现，未批准舍弃"
    if prop in FIXED:
        return "explicit_tradeoff", None, FIXED[prop]
    if prop in BGA:
        return None
    if prop and (prop.startswith("model") or prop in {"solderBumpModeling", "viaModeling"}):
        if "bump" in location.lower() or "bump" in prop.lower():
            return (
                "implementation_gap",
                None,
                "《BGA与Bumps建模表达》要求 Isotropic Cuboid，当前为正交等效层",
            )
        return "gap", None, "当前建模表达未完整开放；不属于已确认的功能取舍"
    return None
