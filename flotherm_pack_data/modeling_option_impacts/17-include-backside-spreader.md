# Include Backside Spreader

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `backsideSpreader.includeBacksideSpreader` |
| 值 | `false` / `true` |
| 模板 | Wirebond PBGA |
| 默认 | `false` |

## 建模影响

启用后：

- 增加 `back_spreader` cuboid；
- 将原来单个 `bottom_trace` 替换成 `bot_trace1..4`，在 spreader 区域形成开孔；
- 不改变 die、die flag、焊球或 thermal vias；
- 默认使用已经存在的铜/trace 等材料，没有新增材料定义。

## 几何规则

Spreader 由长度 `Lspr`、宽度 `Wspr`、厚度 `tspr` 定义并居中：

```text
x0 = -Lspr/2
y0 = -Wspr/2
```

底部 trace 的开孔 `(Lbt,Wbt)` 使用矩形环四段分解：

```text
left/right width = (Ltrace - Lbt)/2
top/bottom depth = (Wtrace - Wbt)/2
```

这避免 spreader 与 bottom trace 在相同体积内重叠。

## 证据

- `../templates/wirebond_pbga/xml_variations/option_switches/opt_v2_c008_includebacksidespreader_true/`
