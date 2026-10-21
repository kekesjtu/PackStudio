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
    if "stiffener" in (prop or "").lower():
        return "gap", "G05", "顶盖 stiffener 分支缺失"
    if location in {"core_vias", "upper_built_up_region", "lower_built_up_region"}:
        return "deferred", "C01", "ADR19 与原生默认值研究已记录未采用的显式基板分支"
    if template == "pbga_fc" and location == "metal_layers":
        return "deferred", "C01", "默认采用整体等效基板，未开放显式金属层栈"
    if prop in {"nonUniformDieHeat", "nonUniformDieHeatDialog"}:
        return "explicit_tradeoff", None, "ADR27：八类模板仅均匀体热源，不实现非均匀热源"
    if location == "die" and label == "Click To Edit":
        return "explicit_tradeoff", None, "ADR27：不实现非均匀热源编辑器"
    if prop in {"userDefinedLeadframeCoverage", "leadframeCoveragePercentage"}:
        return "explicit_tradeoff", None, "ADR27：不实现自定义覆盖率开关及百分比，固定 B/e"
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
            return "adapted", None, "ADR27：共享居中区域及显式矩阵去孔 request.vias"
    if template == "qfn" and prop == "modelViasAs":
        return "adapted", None, "ADR27：启用/禁用开关，启用后离散表达，不提供 lumped"
    if prop in FIXED:
        return "explicit_tradeoff", None, FIXED[prop]
    if prop and (prop.startswith("model") or prop in {"solderBumpModeling", "viaModeling"}):
        return "explicit_tradeoff", None, "requirements.md §2.1：仅 BGA 表达提供切换"
    return None
