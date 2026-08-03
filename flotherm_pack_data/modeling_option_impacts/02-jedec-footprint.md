# JEDEC Footprint

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `new_package.jedecFootprint`、`new_package.lqfpJedecFootprint`、`new_package.sopJedecFootprint` |
| 模板 | 7 类标准外形模板 |
| 可见条件 | `outlineType = standardOutline` |
| 证据 | 每类 3 个代表预设；完整 ID 列表来自 `ui.json` |

## 建模影响

JEDEC Footprint 不是单个尺寸缩放，而是一个参数包查表。一次选择可同时改变：

- 封装长宽、高度、基板/塑封体厚度；
- die、die flag、DAP、leadframe、焊线包络；
- 焊球、引脚、vias 的数量、pitch、直径和排布；
- 等效材料的体积分数、密度、比热和方向导热率；
- 网格包络和最大网格尺寸。

因此准确规则是：

```text
parameter_bundle = JEDEC_PRESETS[template_id][footprint_id]
```

而不是：

```text
new_geometry = baseline_geometry * scale
```

## 代表性证据

- FBGA 从 24/25 球基准切换到 100、324 系列时，焊球/via 实体数和 bondwire 等效材料
  同时变化。
- QFN 从 `12X12_100` 切换至 `6X6_36`、`3X3_8` 时，离散 lead/solder 数量、DAP、
  die 和四套 bondwire 材料共同变化。
- Flip-chip 预设仍保持一个等效 solder-ball block，但包络、体积分数、bumps 和 die
  尺寸会变化。

## 数据边界

当前只导出了每模板 3 个代表预设，足以证明“查表参数包”语义，但不足以从结果反推出
所有 UI 中列出的预设参数。PackStudio 应维护显式 preset 数据表，并把模板生成公式与
preset 数据分离。

## 证据

- `../templates/*/ui.json`
- `../templates/*/xml_variations/option_switches/jed_v2_*/`
