# Depopulated Center

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `solderBallDepopulation.depopulatedCenter` |
| 值 | `false` / `true` |
| 依赖参数 | `numberFullyPopulatedRowsMDp`, `numberFullyPopulatedRowsMEp` |
| 模板 | FBGA/FSBGA、Flip-chip CBGA/PBGA、Wirebond PBGA |
| 默认 | `false` |

该选项保留外周若干完整行，去掉中央矩形。当前案例把 MDp、MEp 都初始化为 2，表示 x、y
两侧各保留一行。

## 离散规则

```text
rx = MDp/2
ry = MEp/2
keep(i,j) = i < rx or i >= Nx-rx or j < ry or j >= Ny-ry
N_active = Nx*Ny - (Nx-2*rx)*(Ny-2*ry)
```

上式以 0-based 索引书写，并假设 MDp/MEp 为偶数。FBGA 5×5、`rx=ry=1` 时保留外圈
16 个，删除中央 3×3 的 9 个球。其 9 个对应 thermal via 也删除。

由于 FBGA 默认 `Number of Bond Wires equals Solder Balls=yes`，bondwire 材料同时从
25 wires 重算为 16 wires；公式和数值见
[Bond Wire Count Mode](25-bond-wire-count-mode.md)。

## 等效层的四块分解

设每侧保留 `rx,ry` 行，外包络为 `Lx,Ly`。边框物理宽度：

```text
Tx = (rx-1)*px + d
Ty = (ry-1)*py + d
Linner = Lx - 2*Tx
Winner = Ly - 2*Ty
A_frame = Lx*Ly - Linner*Winner
```

PACK 用四个不重叠块表示边框：左右两块 `Tx×Ly`，上下两块
`Linner×Ty`。四块共用按整个边框反算的材料：

```text
phi_frame = N_active*pi*d^2/(4*A_frame)
k_normal  = phi_frame*k_solder + (1-phi_frame)*k_air
k_in_plane = k_air
```

rho、cp 按通用质量加权公式计算。

### 7×7 精确案例

`d=0.5 mm`、`p=0.8 mm`、`Lx=Ly=5.3 mm`、`rx=ry=1`：

```text
N_active = 49-25 = 24
A_frame = 5.3^2 - 4.3^2 = 9.6 mm^2
phi_frame = 24*pi*0.5^2/(4*9.6) = 0.490873852123
k_normal = 24.9987672655 W/(m*K)
rho = 4123.93165694 kg/m^3
cp = 150.122878694 J/(kg*K)
```

注意 `k_normal` 高于满阵列整包络的 17.45，因为同样的外圈球被放进更小的边框体积；这
不是焊料总量增加。

## 实现约束

- 校验 `2*rx<Nx`、`2*ry<Ny`；否则中央空区不存在。
- 若 MDp/MEp 的 UI 含义允许奇数，必须先定义两侧如何分配，当前样本未覆盖。
- PackStudio 当前采用此类中央去球，而不采用任意 map；它应与 Central Balls 分开建模。

## 证据

- `../templates/chip_array/xml_variations/option_switches/opt_v2_c004_depopulatedcenter_true/`
- `../templates/cbga_fc/xml_variations/option_switches/opt_v2_c005_depopulatedcenter_true/`
- `../templates/pbga_fc/xml_variations/option_switches/opt_v2_c005_depopulatedcenter_true/`
- `../templates/pbga_wb/xml_variations/option_switches/opt_v2_c005_depopulatedcenter_true/`
