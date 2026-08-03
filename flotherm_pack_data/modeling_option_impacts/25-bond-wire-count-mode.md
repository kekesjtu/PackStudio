# Number of Bond Wires equals Solder Balls

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `bondWires.numberBondWiresEqualsSolderBalls` |
| 值 | `yes` / `no` |
| 模板 | FBGA/FSBGA |
| 默认 | `yes` |

## 计数来源

```text
yes: N_wire = 当前有效 solder-ball 数量
no:  N_wire = bondWires.numberOfBondWiresNw
```

参考分支先把显式 `numberOfBondWiresNw` 初始化为 16：当 flag 为 yes 时仍使用基准 5×5
焊球的 25；切换为 no 后才使用 16。

## 几何与材料影响

两种状态都保留相同的 8 个 bondwire 等效 cuboid；数量只进入金属体积分数，继而改变两种
orthotropic bondwire 材料。对固定的等效块几何，体积分数与 wire 数量线性：

```text
phi_w(N) = V_all_wires / V_equivalent_blocks
         = N*A_wire*l_effective / V_equivalent_blocks
A_wire   = pi*d_wire^2/4
```

当前几何可精确写为：

```text
phi_w(N) = (N/25)*0.102265385859043
```

因此 `phi_w(16)=0.0654498469497874`，两者之比精确为 16/25。`l_effective` 是 PACK
等效 wire 路径长度；当前样本只验证了固定几何下的线性关系，改变 pad extent 后应从实际
路径重新计算，不能继续使用上述常数。

## 材料公式

金属为 Gold (Pure)，基体为 Epoxy Overmold (Typical)：

```text
Gold: rho=19300, cp=132, k=296
Mold: rho=1820,  cp=882, k=0.68

k_high = phi_w*k_gold + (1-phi_w)*k_mold
k_low  = k_mold
rho    = phi_w*rho_gold + (1-phi_w)*rho_mold
cp     = (phi_w*rho_gold*cp_gold
         +(1-phi_w)*rho_mold*cp_mold) / rho
```

| N | phi_w | k_high | rho | cp |
|---:|---:|---:|---:|---:|
| 25 | 0.102265385859 | 30.8810137519 | 3607.59894482 | 471.674051092 |
| 16 | 0.065449846950 | 20.0086488012 | 2964.06332468 | 562.375744098 |

`bondwire1` 的高导方向为 x、z，`bondwire2` 为 y、z；另一平面方向保持 0.68。

## 与去球选项的联动

已采集的单变量案例给出以下实际计数语义：

- 满 5×5 main array：25 wires；
- main stagger 后虽只剩 13 个离散球，bondwire 材料仍按名义 25 wires；
- 中央 3×3 depopulation 后 main array 剩 16 个，材料按 16 wires 重算；
- 空 solder-ball map 使材料退化为 0 wires；
- 额外 2×2 central balls 不改变原 bondwire 材料。

因此这里的 “Solder Balls” 指 main-array 的逻辑计数：会响应 depopulation/map，但不把
stagger 的棋盘格折减或独立 central array 计入。组合选项的应用顺序仍需组合案例验证。

## 证据

- `../templates/fbga_fsbga/xml_variations/option_switches/opt_v2_c004_numberbondwiresequalssolderb_no/`
- `../templates/fbga_fsbga/validation/branch_baselines/br_v2_bondwires_numberbondwiresequalssolderballs/`
