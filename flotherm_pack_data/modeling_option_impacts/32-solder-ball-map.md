# Solder Ball Map

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `solderBalls.solderBallMap` |
| 值 | `false` / `true` |
| 模板 | FBGA/FSBGA、Flip-chip CBGA/PBGA、Wirebond PBGA |
| 默认 | `false` |

## 正确语义

该布尔值是“改用用户编辑的二维占位图”的模式开关。真正决定几何的是另一个 map payload：

```text
occupied(i,j) in {0,1}
N_active = sum_i sum_j occupied(i,j)
```

离散模式只为 `occupied=1` 的位置生成球；等效模式必须根据有效位置的空间分区计算包络与
局部体积分数。仅有 `true` 不能恢复占位图。

## 当前单变量案例的特殊结果

FloSCRIPT 只写入 `solderBallMap=true`，没有记录 map 编辑器内容。因此导出表现为：

- FBGA：删除全部 25 个 main solder-ball cuboid；
- 三个等效 BGA：删除唯一的 `solder_ball` 等效块，并以未引用的纯 solder 材料替换原
  `Solder_ball` 等效材料；
- 其他封装几何不因布尔值直接移动。

这只是“空 map”的数据边界，绝不能实现为 `true => 删除全部焊球`。

FBGA 中 `Number of Bond Wires equals Solder Balls=yes` 还把 wire 数视为 0，使两个
bondwire 材料退化为纯 mold (`rho=1820, cp=882, k=0.68`)；thermal vias 并未随空 map
删除。该联动进一步说明 map payload 必须在生成 bondwire 材料前解析。

## 任意 map 的精确计算建议

离散模式公式是确定的。若要生成单一整包络等效层：

```text
Lx = (imax-imin)*px + d
Ly = (jmax-jmin)*py + d
phi = N_active*pi*d^2/(4*Lx*Ly)
```

但对于稀疏或不连通 map，单包络会在空区制造虚假 z 向导热。高可信实现应把 occupied
cells 分解为若干不重叠矩形，分别用各自 `N_region/A_region` 计算材料；这属于 PackStudio
扩展算法，不是当前空-map 样本已验证的 PACK 内部实现。

## PackStudio 取舍

当前需求只保留“中央焊球 + 焊球去除”，不提供复杂 map 编辑器。前端不暴露此 option，
但导入器遇到 map 时应报“暂不支持”，不能静默生成满阵列或空阵列。

## 证据

- `../templates/fbga_fsbga/xml_variations/option_switches/opt_v2_c003_solderballmap_true/`
- `../templates/flip_chip_cbga/xml_variations/option_switches/opt_v2_c004_solderballmap_true/`
- `../templates/flip_chip_pbga/xml_variations/option_switches/opt_v2_c004_solderballmap_true/`
- `../templates/wirebond_pbga/xml_variations/option_switches/opt_v2_c004_solderballmap_true/`
