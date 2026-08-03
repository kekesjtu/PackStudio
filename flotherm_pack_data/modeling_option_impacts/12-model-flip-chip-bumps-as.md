# Model Flip Chip Bumps As

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `modelingOptions.modelFlipChipBumpsAs` |
| 值 | `isotropicCuboid` / `collapsedCuboid` |
| 模板 | Flip-chip CBGA、Flip-chip PBGA |
| 默认 | `isotropicCuboid` |

## Isotropic Cuboid

`fc_bumps` 保持输入高度 `h_bump=0.1 mm`，die 位于 bumps 顶面之上。材料是 bump 与
underfill/air 的各向同性体积分数混合，公式见 [Underfill](10-underfill.md)。

## Collapsed Cuboid

FloXML 仍保留 `fc_bumps` 的名义尺寸和材料，但增加：

```xml
<collapse>
  <type>...</type>
  <direction>...</direction>
</collapse>
```

同时 die、DieSource、结温点和封装顶部整体下移恰好 `h_bump=0.1 mm`。因此求解几何中
该层被压缩为零厚度界面，名义 cuboid 仅承载 collapsed 属性。

```text
z_die_collapsed = z_die_isotropic - h_bump
z_top_collapsed = z_top_isotropic - h_bump
```

材料数值不变；z 网格包络及最大单元尺寸随总高度缩短而重算。

## PackStudio 取舍

项目决策明确不采用 collapsed 或 PACK 的各向同性 bumps 表达。PackStudio 固定输出有
厚度的正交各向异性 bumps+underfill 层，前端不应暴露此选项。

## 证据

- `../templates/flip_chip_cbga/xml_variations/option_switches/opt_v2_c007_modelflipchipbumpsas_collapsedcuboid/`
- `../templates/flip_chip_pbga/xml_variations/option_switches/opt_v2_c008_modelflipchipbumpsas_collapsedcuboid/`
