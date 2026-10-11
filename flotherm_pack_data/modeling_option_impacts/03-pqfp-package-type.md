# PQFP Package Type

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `new_package.pqfpPackageType` |
| 值 | `lqfp` / `mqfp` / `tqfp` |
| 模板 | QFP Family |
| 默认 | `lqfp` |

## 建模影响

该选项切换 QFP 的标准族，并改变后续 JEDEC Footprint 的候选集合。单变量默认导出表明，
即使不另选 footprint，PACK 也会载入该族的默认参数包，改变封装体、引脚、die flag、
tie bars、焊线和网格。

- `MQFP` 案例有 239 个叶值变化，56 个实体签名变化。
- `TQFP` 案例有 62 个叶值变化，51 个实体签名变化。
- 两个案例都重新计算 `bondwire1/2`，但不改变建模算法类型。

## 计算规则

该选项本身是二级查表键：

```text
footprint_table = QFP_PRESETS[pqfp_package_type]
resolved = footprint_table[default_or_selected_footprint]
```

它不是固定的 LQFP→MQFP 或 LQFP→TQFP 比例公式。

## PackStudio 结论

前端可将三族保留为筛选器；生产模型必须由最终解析后的尺寸和数量生成，不能在已有
LQFP 模型上做统一缩放。

## 证据

- `../templates/pqfp/ui.json`
- `../templates/pqfp/xml_variations/option_switches/opt_v2_c002_pqfppackagetype_mqfp/`
- `../templates/pqfp/xml_variations/option_switches/opt_v2_c003_pqfppackagetype_tqfp/`
