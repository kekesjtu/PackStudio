"""Reviewed scope rules for the offline PACK option inventory."""

FIXED = {
    "outlineType": "requirements.md §2.1：固定 standard_outline",
    "dieType": "requirements.md §2.1：固定 actual_type",
    "substrateLayer": "ADR19：四层分支留库，生产保持两层能力",
    "exposedPad": "requirements.md §2.1：改用 thermal_land，不保留 starter 开关",
    "staggeredMatrix": "ADR5/6/12：仅正交阵列与项目中央/去球规则",
    "solderBallMap": "ADR6：不提供任意坐标 solder-ball map",
    "underfill": "ADR6 §3：固定有 underfill 的厚等效层，移除开关",
    "arrayType": "TASK5/ADR12：凸点固定全阵列与总数驱动等效层",
    "numberOfBumpsInXMDC4": "TASK5/ADR12：凸点采用总数驱动，不提供独立行列",
    "numberOfBumpsInYMEC4": "TASK5/ADR12：凸点采用总数驱动，不提供独立行列",
    "enableDieFlush": "ADR5：单独塑封保留顶部盖层、淹没芯片",
    "localizeGrid": "requirements.md §2/4、ADR25：最大网格控制与目标软件配置",
    "numberOfDiscreteBondwireSteps": "pack-material-couplings.md QFN 节：保留单步等效包络",
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
    if location == "backside_spreader":
        return "gap", "G01", "背面扩散片和底部开孔未消费原生默认值"
    if "stiffener" in (prop or "").lower():
        return "gap", "G05", "顶盖 stiffener 分支缺失"
    if location in {"core_vias", "upper_built_up_region", "lower_built_up_region"}:
        return "deferred", "C01", "ADR19 与原生默认值研究已记录未采用的显式基板分支"
    if template == "pbga_fc" and location == "metal_layers":
        return "deferred", "C01", "默认采用整体等效基板，未开放显式金属层栈"
    if prop in {"nonUniformDieHeat", "nonUniformDieHeatDialog"}:
        return "gap", "G06", "没有非均匀热源入口；体源/面源取舍不能替代空间分布决策"
    if location == "die" and label == "Click To Edit":
        return "gap", "G06", "非均匀热源编辑器缺失"
    if prop in {"userDefinedLeadframeCoverage", "leadframeCoveragePercentage"}:
        return "gap", "G03", "引线框覆盖率只能按 B/e 计算"
    if template == "bare_die" and prop == "dieMaterial":
        return "gap", "G11", "截图 Si/GaAs 二选一，当前仅 silicon"
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
            return "gap", "G09", "热过孔去孔编辑器缺失"
    if template == "qfn" and location == "vias":
        return "gap", "G10", "QFN 保留 ignored 基线，整组过孔配置未开放"
    if prop in FIXED:
        return "explicit_tradeoff", None, FIXED[prop]
    if prop and (prop.startswith("model") or prop in {"solderBumpModeling", "viaModeling"}):
        return "explicit_tradeoff", None, "requirements.md §2.1：仅 BGA 表达提供切换"
    return None
