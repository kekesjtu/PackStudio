# Top Cover

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `new_package.topCover` |
| 值 | `bareDie` / `lid` / `plate` / `encapsulant` |
| 模板 | Flip-chip CBGA、Flip-chip PBGA |
| 默认 | `bareDie` |

## 各值的建模结果

### Bare Die

不增加顶部覆盖物；die 顶面直接成为封装顶部热边界。Slug、stiffener、die-flush 等依赖
顶部结构的选项不可用或没有意义。

### Lid

增加：

- `Lid` assembly：顶部 lid 和四周 skirt/侧壁；
- `Lid_Adhesive` assembly：四段环形粘接层；
- die 顶部 `die_attach`/grease 热界面层；
- Aluminum、Flip-Chip Cap Grease、Stiffener Adhesive 默认材料。

### Plate

增加单个 `thermal_plate` 和 die 顶部 grease/attach 层，不增加 lid skirt。它比 lid 少一套
四周框架和框架粘接几何。

### Encapsulant

增加覆盖 die 和 bumps 区域的单个 `encapsulant` cuboid，默认材料为
`Epoxy Overmold (Typical)`。

## 矩形几何规则

所有顶部主体相对封装中心对齐：

```text
x0 = -L / 2
y0 = -W / 2
```

若 lid 或 adhesive 使用外框 `(L, W)` 和内腔 `(Lc, Wc)`，矩形环可无重叠地分解为：

```text
left/right width = (L - Lc) / 2
top/bottom depth = (W - Wc) / 2
```

四段 cuboid 的 z 尺寸等于相应 lid skirt 或 adhesive 厚度。该分解与导出的
`lid_*`、`lid_adhesive*` 结构一致。

## 联动

- `Stiffener` 只在 lid 分支有效，并会替换/重组部分 lid skirt。
- `Enable Die Flush` 只在 encapsulant 分支有明确效果。
- `Include Slug` 在 Flip-chip 模板要求 `topCover=encapsulant`。

## 证据

- `../templates/flip_chip_cbga/xml_variations/option_switches/opt_v2_c002_topcover_lid/`
- `../templates/flip_chip_cbga/xml_variations/option_switches/opt_v2_c003_topcover_plate/`
- `../templates/flip_chip_cbga/xml_variations/option_switches/opt_v2_c004_topcover_encapsulant/`
- `../templates/flip_chip_pbga/xml_variations/option_switches/opt_v2_c002_topcover_lid/`
