# Include Thermal Land and Solder

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `thermalLandAndSolder.includeThermalLandAndSolder` |
| 值 | `false` / `true` |
| 模板 | QFP、SOIC |
| 默认 | `false` |

## 建模影响

选择 true 只在封装底部增加两个顶层 cuboid：`land` 和 `solder`。内部 die flag、die、
bondwire、leadframe 和 encapsulant 均不移动。这与会下移内部堆叠的
[Exposed Pad](06-exposed-pad.md) 是不同结构分支。

两个块的 x/y 尺寸与 die flag 相同并以原点居中：

```text
L_land=L_solder=L_flag
W_land=W_solder=W_flag
z_land=-t_land
z_solder=0
```

两个模板都把 `t_land` 初始化为 0.05 mm。导出还满足：

```text
t_solder = t_lead - t_land
```

| 模板 | XY (mm) | t_lead | t_land | t_solder |
|---|---|---:|---:|---:|
| QFP | 2.94×2.94 | 0.15 | 0.05 | 0.10 |
| SOIC | 1.7748×1.3716 | 0.20 | 0.05 | 0.15 |

厚度关系由两个模板共同支持，列为强推断；PACK 未公开公式。

## 材料数据边界

当前 branch 初始化只给 land thickness，基准的 land/solder 材料都仍是 `No Attachment`。
结果 FloXML 中两个 cuboid 没有 `<material>`，也没有新增材料属性。因此这些案例证明了几何
规则，但不是可直接求解的完整热路径。

高可信实现必须在 include=true 时要求：

```text
land_material != No Attachment
solder_material != No Attachment
0 < t_land < t_lead
```

若使用常见默认，可分别选择铜 land 与 Sn63/Pb37 solder，但这属于 PackStudio 默认决策，
不是当前单变量样本已经导出的材料事实。

## 证据

- `../templates/pqfp/xml_variations/option_switches/opt_v2_c003_includethermallandandsolder_true/`
- `../templates/sop/xml_variations/option_switches/opt_v2_c003_includethermallandandsolder_true/`
