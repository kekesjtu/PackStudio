# Flipped Die

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `die.flippedDie` |
| 值 | `false` / `true` |
| 模板 | Bare Die |
| 默认 | `false` |

## 建模影响

Die cuboid 的尺寸、位置和 silicon 材料不变。变化集中在热源附着面和结温监控点：

| 字段 | false | true |
|---|---|---|
| `DieSource.attachment_side` | `low_side` | `high_side` |
| `DieSource.collapse.type` | `high_face` | `low_face` |
| `DieJunction_Temp.z` | 0.2189 mm | 0.0011 mm |

因此它表示有源面/结温采样面的翻转，而不是把长方体在空间中旋转。监控点距对应 die
表面保留一个很小的内部偏置，避免落在共享边界上。

## PackStudio 结论

几何实体可复用；需要翻转 source attachment side 和 junction monitor 的 z 面选择。

## 证据

- `../templates/bare_die/xml_variations/option_switches/opt_v2_c002_flippeddie_true/`
