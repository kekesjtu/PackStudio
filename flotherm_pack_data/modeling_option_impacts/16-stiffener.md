# Stiffener

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `topCover.stiffener` |
| 值 | `no` / `yes` |
| 模板 | Flip-chip CBGA、Flip-chip PBGA |
| 前提 | `topCover=lid` |

## 建模影响

启用后增加：

- `Stiffener` assembly：四个不锈钢矩形环段；
- `Stiffener_Adhesive` assembly：四个粘接环段；
- `Steel Stainless-302 (Cr18/Ni8)` 材料。

同时移除/替换原 lid 的四个竖直侧壁块，说明 stiffener 不是简单叠加件，而是 lid 周边
支撑结构的替代分支。lid 顶板及 die 顶部 TIM 仍保留。

## 环形分解公式

外形 `(Ls, Ws)`、腔体 `(Lsc, Wsc)`：

```text
left/right width = (Ls - Lsc) / 2
top/bottom depth = (Ws - Wsc) / 2
```

四段按中心对称放置，z 尺寸为 stiffener thickness。Adhesive 使用相同平面分解和独立
adhesive thickness。

## 证据

- `../templates/flip_chip_cbga/xml_variations/option_switches/opt_v2_c010_stiffener_yes/`
- `../templates/flip_chip_pbga/xml_variations/option_switches/opt_v2_c011_stiffener_yes/`
