# Solder Ball Staggered Matrix

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `solderBalls.staggeredMatrix` |
| 值 | `false` / `true` |
| 模板 | FBGA/FSBGA、Flip-chip CBGA/PBGA、Wirebond PBGA |
| 默认 | `false` |

## 离散模式

PACK 保留从 1 开始编号且行列同奇偶的棋盘格位置：

```text
occupied(i,j) = 1 if (i+j) mod 2 = 0
N_active = ceil(Nx*Ny/2)
```

FBGA 5×5 样本保留 13 个球：`(1,1),(1,3),...,(5,5)`，删除其余 12 个。与 main
ball 一一对应的 12 个 thermal via 也同时删除；bondwire 等效材料仍按名义 25 wires，
未随 stagger 数量减半。

## 等效模式

Flip-chip 7×7 和 Wirebond 11×11 的等效块尺寸完全不变。PACK 没有用奇数阵列的
`ceil(N/2)`，而是精确采用：

```text
phi_staggered = 0.5*phi_full
```

再以 solder/air 公式重算 `k_normal`、rho、cp；`k_in_plane` 仍为 0.0261。

| 模板 | k_normal: full → staggered | rho: full → staggered |
|---|---|---|
| Flip-chip 7×7 | 17.4509586118 → 8.73852930588 | 2877.85406772 → 1439.50773386 |
| Wirebond 11×11 | 15.0591894555 → 7.54264472773 | 2482.99377369 → 1242.07758684 |

这等价于 24.5/60.5 个球的连续体积分数，是等效近似而非离散计数。

## PackStudio 取舍

当前需求不提供复杂 stagger 选项。生成器不需要复刻这条分支；文档保留它用于解释 PACK
样本以及未来导入时给出明确的不支持提示。

## 证据

- `../templates/chip_array/xml_variations/option_switches/opt_v2_c002_staggeredmatrix_true/`
- `../templates/cbga_fc/xml_variations/option_switches/opt_v2_c003_staggeredmatrix_true/`
- `../templates/pbga_fc/xml_variations/option_switches/opt_v2_c003_staggeredmatrix_true/`
- `../templates/pbga_wb/xml_variations/option_switches/opt_v2_c003_staggeredmatrix_true/`
