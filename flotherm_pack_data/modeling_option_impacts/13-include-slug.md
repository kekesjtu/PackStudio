# Include Slug

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | Flip-chip: `dropInSlug.includeSlug`; WB-PBGA: `new_package.includeSlug` |
| 值 | `false` / `true` |
| 模板 | Flip-chip CBGA/PBGA、Wirebond PBGA |
| 默认 | `false` |

## 建模影响

启用后增加 `Slug` assembly。参考输出不是一个简单 cuboid，而是：

- `slug_top`：圆形顶部按等面积正方形近似；
- `slug_h1..h4`：中心上部的四段填充；
- `slug_v1..v4`：四周竖直壁；
- `slug_foot_left/right/upper/lower`：向外延伸的四段 foot。

对直径 `Ds` 的圆形 slug top：

```text
s_top = Ds * sqrt(pi) / 2
```

验证分支 `Ds=2 mm` 导出：

```text
s_top = 1.772453850905516 mm
```

若主体外形为 `Lsl × Wsl`，中心方形为 `s_top`：

```text
side_x = (Lsl - s_top) / 2
side_y = (Wsl - s_top) / 2
```

`Lsl=Wsl=4 mm` 时两侧尺寸均为 `1.113773074547242 mm`，与 `slug_h*` 一致。
foot 延伸到 `Lsf × Wsf`：

```text
foot_x = (Lsf - Lsl) / 2
foot_y = (Wsf - Wsl) / 2
```

`4.5-4.0` 的案例得到每侧 `0.25 mm`。

## 材料边界

Wirebond PBGA starter 分支产生 Copper slug。Flip-chip 分支因默认材料仍为
`No Attachment`，几何存在但没有 material 标签；不能把“无材料”理解为最终物理选择。

## 联动

Flip-chip 中该选项要求 `topCover=encapsulant`；Slug adhesive 由独立选项控制。

## 证据

- `../templates/cbga_fc/xml_variations/option_switches/opt_v2_c008_includeslug_true/`
- `../templates/pbga_fc/xml_variations/option_switches/opt_v2_c008_includeslug_true/`
- `../templates/pbga_wb/xml_variations/option_switches/opt_v2_c001_includeslug_true/`
