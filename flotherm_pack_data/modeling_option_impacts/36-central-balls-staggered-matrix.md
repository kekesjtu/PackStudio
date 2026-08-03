# Central Balls Staggered Matrix

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `centralBalls.staggeredMatrix` |
| 值 | `false` / `true` |
| 前提 | `centralBalls.centralBalls=true` |
| 模板 | FBGA/FSBGA、Flip-chip CBGA/PBGA、Wirebond PBGA |
| 默认 | `false` |

## 离散模式

对中央子阵列应用与 main stagger 相同的棋盘格：

```text
keep(i,j) = ((i+j) mod 2 == 0)
N_active = ceil(MDc*MEc/2)
```

2×2 FBGA 分支保留 `center_sball_1_1`、`center_sball_2_2`，删除另两个，几何和纯 solder
材料不变。

## 等效模式

中央包络尺寸不变，PACK 精确使用：

```text
phi_c,staggered = 0.5*phi_c,full
```

随后按 solder/air 公式重算材料。Flip-chip 2×2 案例：

```text
k_normal: 23.6688619082 -> 11.8474809541 W/(m*K)
rho:       3904.37584444 -> 1952.76862222 kg/m^3
cp:         150.136452591 -> 150.391260384 J/(kg*K)
```

这里 2×2 恰好也有一半位置，连续体积分数与离散计数一致。

## PackStudio 取舍

当前产品需求不提供交错中央阵列，只保留规则中央球与中央去球。该字段不进入生成器公开
schema；导入含此字段的 PACK 数据时应提示不支持。

## 证据

- `../templates/fbga_fsbga/xml_variations/option_switches/opt_v2_c006_staggeredmatrix_true/`
- `../templates/flip_chip_cbga/xml_variations/option_switches/opt_v2_c007_staggeredmatrix_true/`
- `../templates/flip_chip_pbga/xml_variations/option_switches/opt_v2_c007_staggeredmatrix_true/`
- `../templates/wirebond_pbga/xml_variations/option_switches/opt_v2_c007_staggeredmatrix_true/`
