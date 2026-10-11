# SOP Package Type

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `new_package.sopPackageType` |
| 值 | `soic/sop/so` / `ssop` / `tsop` / `tssop` |
| 模板 | SOIC Family |
| 默认 | `soic/sop/so` |

## 建模影响

该选项切换 SOP 标准族及其 JEDEC 列表。默认族切换会重新初始化：

- 塑封体长宽高与 standoff；
- die、die flag、tiebar 和 die attach 的位置/尺寸；
- leadframe 几何及自动覆盖率；
- bondwire 包络和等效材料；
- 网格包络。

单变量差异分别为：SSOP 166、TSOP 160、TSSOP 170 个叶值变化，三者均保持原有
实体种类，但 35 个主要实体的几何签名变化。

## 计算规则

```text
footprint_table = SOP_PRESETS[sop_package_type]
resolved = footprint_table[default_or_selected_footprint]
```

族之间不是统一比例缩放。leadframe 与 bondwire 等效材料在解析具体参数后按各自文件中
记录的体积分数公式重算。

## 证据

- `../templates/sop/ui.json`
- `../templates/sop/xml_variations/option_switches/opt_v2_c002_soppackagetype_ssop/`
- `../templates/sop/xml_variations/option_switches/opt_v2_c003_soppackagetype_tsop/`
- `../templates/sop/xml_variations/option_switches/opt_v2_c004_soppackagetype_tssop/`
