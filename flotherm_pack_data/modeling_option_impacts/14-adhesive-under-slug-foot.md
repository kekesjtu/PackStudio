# Adhesive Present Under Slug Foot

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `dropInSlug.adhesivePresentUnderSlugFoot` |
| 值 | `false` / `true` |
| 模板 | Flip-chip CBGA、Flip-chip PBGA |
| 前提 | `topCover=encapsulant` 且 `includeSlug=true` |

## 建模影响

启用后增加 `Slug Adhesive` assembly，包含四个 cuboid：

```text
slug_adh_left
slug_adh_right
slug_adh_upper
slug_adh_lower
```

每段位于相应 slug foot 下方；平面尺寸与 foot 环形分解一致，z 尺寸为 adhesive
thickness。关闭时这些块完全不存在，slug 金属几何本身不变。

对于主体/foot 尺寸 `(Lsl,Wsl)`、`(Lsf,Wsf)`：

```text
adh_left/right width = (Lsf - Lsl) / 2
adh_upper/lower depth = (Wsf - Wsl) / 2
```

## 数据边界

验证分支没有选择非默认 adhesive material，因此新增 cuboid 无 material 标签。当前证据
确认几何和依赖关系，但不能据此指定 PackStudio 默认材料。

## 证据

- `../templates/flip_chip_cbga/xml_variations/option_switches/opt_v2_c009_adhesivepresentunderslugfoot_true/`
- `../templates/flip_chip_pbga/xml_variations/option_switches/opt_v2_c011_adhesivepresentunderslugfoot_true/`
