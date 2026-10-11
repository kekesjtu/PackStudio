"""Give native property states explicit semantics and expand implicit table positions."""

import re


def scalar(value: str, native_type: str = ""):
    if value in {"CHECKED", "UNCHECKED"}:
        return value == "CHECKED"
    if "NumericValue" in native_type:
        return int(value) if "@H@" in native_type else float(value)
    return value


def raw_values(group: dict) -> dict:
    return {p["name"]: p["value"] for p in group["properties"]}


def metal_rows(group: dict, groups: list[dict]) -> list[dict]:
    source = group.get("metal_layer_rows") or []
    substrate = next((g for g in groups if "substrateThicknessA2" in raw_values(g)), None)
    thickness = float(raw_values(substrate)["substrateThicknessA2"]) / 1000 if substrate else 0
    result = []
    for index, row in enumerate(source):
        if row["thickness_m"] is None and row["coverage_percent"] is None:
            result.append(
                {
                    "index": index,
                    "status": "not_applicable",
                    "comment": "原生表中的空槽位，不创建金属层。",
                }
            )
            continue
        if row["thickness_m"] is None or row["coverage_percent"] is None:
            raise ValueError("partially populated native metal layer")
        depth = row["depth_m"]
        comment = "原生金属表；深度从基板顶面到金属层顶面，长度以米计。"
        if depth is None:
            if index == 0:
                depth = 0.0
                comment += "顶层自动贴顶：depth=0。"
            elif index == len(source) - 1:
                depth = thickness - row["thickness_m"]
                comment += "底层自动贴底：depth=substrateThickness-layerThickness。"
            else:
                raise ValueError("unreviewed automatic inner-layer depth")
        result.append(
            {
                "index": index,
                "status": "specified",
                "depth_m": depth,
                "thickness_m": row["thickness_m"],
                "coverage_percent": row["coverage_percent"],
                "z_from_substrate_bottom_m": thickness - depth - row["thickness_m"],
                "comment": comment + " z=substrateThickness-depth-layerThickness。",
                **(
                    {"disconnect_to_vias": row["disconnect_to_vias"]}
                    if "disconnect_to_vias" in row
                    else {}
                ),
            }
        )
    return result


def chip_wire_count(groups: list[dict]) -> int:
    values = {g["name"]: raw_values(g) for g in groups}
    balls = values["solderBalls"]
    ball_group = next(g for g in groups if g["name"] == "solderBalls")
    if balls["solderBallMap"] == "CHECKED":
        return len(ball_group["solder_ball_map"])
    count = int(balls["numberOfSolderBallsInXMD"]) * int(balls["numberOfSolderBallsInYME"])
    depop = values["solderBallDepopulation"]
    if depop["depopulatedCenter"] == "CHECKED":
        count -= (
            int(balls["numberOfSolderBallsInXMD"]) - int(depop["numberFullyPopulatedRowsMDp"])
        ) * (int(balls["numberOfSolderBallsInYME"]) - int(depop["numberFullyPopulatedRowsMEp"]))
    return count


def unspecified(name: str, group: dict, family: str, values: dict) -> tuple[str, str]:
    if group["name"] == "summary":
        return "user_input", "器件限值元数据；PACK 没有给定额定值，需用户输入，不能补零。"
    if not group.get("enabled", True):
        return "not_applicable", "当前原生向导分支未启用此组；切换分支后需重新定义。"
    if family == "pbga_fc" and group["name"] in {
        "coreVias",
        "upperBuiltUpRegion",
        "lowerBuiltUpRegion",
    }:
        return "not_applicable", "原生预设采用整体等效基板材料，未定义此显式结构。"
    if group["name"] == "backsideSpreader" and values["includeBacksideSpreader"] == "UNCHECKED":
        return "not_applicable", "当前分支未勾选背面扩散结构；不创建该结构。"
    if name in {"lengthLml", "widthWml"} and family == "chip_array":
        return "not_applicable", "该字段是顶层金属开孔尺寸，原生默认没有开孔；不是整层尺寸。"
    if name in {"numberOfBumpsInXMDC4", "numberOfBumpsInYMEC4"}:
        return "not_applicable", "非规则 bump 阵列按 totalNumberOfBumpsMNC4 定义，未指定矩阵行列。"
    if name in {"numberOfLeadsOnLeftRightME", "pitchInYDirectionEy"} and family == "QFN":
        return "not_applicable", "此两边引脚预设没有左右引脚；该方向的节距不适用。"
    if "stiffener" in name.lower() and values.get("stiffener") == "2":
        return "not_applicable", "顶盖子分支的 stiffener=no，相关尺寸未定义。"
    raise ValueError(f"unclassified unset property: {family}/{group['name']}/{name}")


def property_record(prop: dict, group: dict, family: str, groups: list[dict]) -> dict:
    name, raw, kind = prop["name"], prop["value"], prop["native_type"]
    details = group.get("property_details", {}).get(name, {})
    values = raw_values(group)
    record = {
        "status": "specified",
        "kind": "text",
        "native": {"type": kind, "state": prop["native_state"]},
        "comment": "来自 .des 加载、原生构造/初始化及 setWizardData 后的参数。",
    }
    if raw is not None:
        record["native"]["serialized_value"] = raw
    if "FlopackClickToEditProperty" in kind:
        record.update(
            kind="action",
            status="action",
            comment="编辑按钮；参数数据保存在对应 Dialog 属性中，按钮本身没有数值。",
        )
        return record
    if details.get("enum_choices"):
        record.update(
            kind="enum",
            value=details["enum_label"],
            choices=details["enum_choices"],
            index=details["enum_index"],
        )
    elif "TableProperty" in kind:
        record.update(
            kind="table",
            value=metal_rows(group, groups),
            comment="已展开原生表内容和自动层位置；空行明确标记为不适用。",
        )
    elif "structured_value" in details:
        record.update(kind="structured", value=details["structured_value"])
        if "DepopulationProperty" in kind:
            record["comment"] = (
                "原生保存的坐标列表，column=X、row=Y；非空列表是保留的球位，不是删除名单。"
                "是否使用仍取决于 depopulatedCenter 与模型实现分支，不能自动启用。"
            )
        else:
            record["comment"] = "已展开原生热源对话框；当前预设均未定义区域或功率矩阵。"
    elif "SolderBallMapProperty" in kind:
        record.update(
            kind="structured",
            value=group.get("solder_ball_map", []),
            comment="已展开原生逐球名称与位置（米）；空列表表示未定义独立球位图。",
        )
    elif raw is None:
        if name == "numberOfBondWiresNw" and family == "chip_array":
            record.update(
                kind="integer",
                status="calculated",
                value=chip_wire_count(groups),
                unit="count",
                comment=(
                    "numberBondWiresEqualsSolderBalls=yes：取原生焊球计数。"
                    "启用球位图时取列表长度；否则 MD*ME，若 depopulatedCenter=true，"
                    "再减 (MD-MDp)*(ME-MEp)。原生 realise RVA 0x3ff0/0x4040；"
                    "本计数不读取未启用的自定义坐标列表或 centralBalls。"
                ),
            )
        elif name == "leadframeCoveragePercentage":
            record.update(
                kind="number",
                status="calculated",
                unit="percent",
                value=100 * float(values["leadWidthB"]) / float(values["pitchE"]),
                comment="userDefinedLeadframeCoverage=noDefaultIsBe，默认覆盖率=B/e；百分数=100*leadWidthB/pitchE。",
            )
        elif name in group.get("effective_parameters", {}):
            record.update(
                kind="integer",
                status="calculated",
                unit="count",
                value=group["effective_parameters"][name],
                comment=(
                    "来自 QFNModelingOptions 原生 getter（RVA 0x31080）；"
                    "存储值<2 时返回1，否则返回存储值。没有读取未初始化属性数值。"
                ),
            )
        else:
            status, comment = unspecified(name, group, family, values)
            record.update(status=status, comment=comment)
    else:
        record["value"] = scalar(raw, kind)
        if "MaterialAttachmentProperty" in kind:
            record.update(kind="material_reference", comment="按原生名称引用独立材料库。")
            if not raw:
                record.pop("value")
                record.update(status="not_specified", comment="原生没有指定可选分支的材料。")
        elif "NumericValue" in kind:
            record["kind"] = "integer" if "@H@" in kind else "number"
            if record["kind"] == "integer":
                record["unit"] = "count"
            elif "coverage" in name.lower() or name.startswith("metalCoverage"):
                record["unit"] = "percent"
            elif "Power" in name or name == "packagePower":
                record["unit"] = values.get("powerUnit", "W")
            elif "Temperature" in name:
                record["unit"] = "native_temperature"
            else:
                record["unit"] = values.get("lengthUnit", "mm")
        elif raw in {"CHECKED", "UNCHECKED"}:
            record["kind"] = "boolean"
    if "value" in record and record["value"] is None:
        raise ValueError(f"unresolved native enum: {family}/{name}")
    if name in {
        "substrateThicknessA2",
        "viaPitchEv",
        "numberOfThermalViasInXNVx",
        "numberOfThermalViasInYNVy",
        "numberOfBondWiresNw",
        "includeBacksideSpreader",
        "bottomTraceHoleLengthLbt",
        "bottomTraceHoleWidthWbt",
        "spreaderLengthLspr",
        "spreaderWidthWspr",
        "spreaderThicknessTspr",
    }:
        record["comment"] += calculation_comment(family, name)
    return record


def calculation_comment(family: str, name: str) -> str:
    if family == "pbga_wb":
        if name == "includeBacksideSpreader":
            return " WB setDieTypeData：有中央去球区时自动启用 backsideSpreader。"
        if name in {"bottomTraceHoleLengthLbt", "bottomTraceHoleWidthWbt"}:
            axis, full = ("MD", "MDp") if "Length" in name else ("ME", "MEp")
            return f" WB setDieTypeData：hole=({axis}-{full}+2)*ballPitchE-ballDiameterB。"
        if name in {"spreaderLengthLspr", "spreaderWidthWspr"}:
            return " WB setLayerData：扩散结构尺寸取对应 bottomTraceHole；4层时再减2mm。"
        if name == "spreaderThicknessTspr":
            return " WB setLayerData：厚度取向导信号层厚度（原生存储 wizard+0x958）。"
        if name == "substrateThicknessA2":
            return (
                " WB setLayerData(RVA 0x40810)：4层=0.56mm；"
                "2层且D<=23mm且E<=30mm为0.36mm，否则0.56mm。"
            )
        if name == "viaPitchEv":
            return " WB setThermalViaData(RVA 0x40990)：间距取焊球 ballPitchE。"
        if name.startswith("numberOfThermalVias"):
            return " WB setThermalViaData：2层每轴5个，4层每轴3个。"
        if name == "numberOfBondWiresNw":
            return (
                " WB actualDie 的 setDieTypeData(RVA 0x40660)："
                "MD*ME减中央去球矩形数量；不能用文件名代替。"
            )
    if family == "chip_array" and name == "substrateThicknessA2":
        return " ChipArray setLayerData(RVA 0xab20)：2层=0.36mm，4层=0.56mm。"
    return ""


def wizard_record(name: str, prop: dict) -> dict:
    value = prop["value"]
    if prop.get("enum_choices"):
        return {
            "value": prop["enum_label"],
            "choices": prop["enum_choices"],
            "comment": "原生向导选项；封装子类型按所选 .des 的家族前缀设置。",
        }
    value = float(value) if re.fullmatch(r"[0-9.]+", value) else scalar(value)
    return {"value": value, "comment": f"原生向导初始化参数 {name}。"}
