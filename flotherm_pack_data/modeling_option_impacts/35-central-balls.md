# Central Balls

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `centralBalls.centralBalls` |
| 值 | `false` / `true` |
| 依赖参数 | `numberCentralRowsMDp`, `numberCentralRowsMEp` |
| 模板 | FBGA/FSBGA、Flip-chip CBGA/PBGA、Wirebond PBGA |
| 默认 | `false` |

该选项在 main solder-ball array 之外增加一个以原点为中心的子阵列。当前案例把两个中央
方向都初始化为 2，因此增加 2×2 个球。

## 离散模式

```text
Nc = MDc*MEc
center_x(i) = (i-(MDc-1)/2)*px
center_y(j) = (j-(MEc-1)/2)*py
s = d*sqrt(pi)/2
```

FBGA 输出独立 `Center_SBall` assembly 和四个纯 Sn63/Pb37 cuboid。它不增加对应 thermal
via，也不改变原 25-wire 的 bondwire 等效材料。

## 等效模式

中央阵列生成一个独立 biaxial cuboid：

```text
Lcx = (MDc-1)*px + d
Lcy = (MEc-1)*py + d
phi_c = MDc*MEc*pi*d^2/(4*Lcx*Lcy)

k_c,normal = phi_c*k_solder + (1-phi_c)*k_air
k_c,in_plane = k_air
rho_c = phi_c*rho_solder + (1-phi_c)*rho_air
cp_c  = (phi_c*rho_solder*cp_solder
        +(1-phi_c)*rho_air*cp_air) / rho_c
```

Flip-chip 的 2×2 案例 `d=0.5 mm`、`p=0.8 mm`：

```text
Lcx=Lcy=1.3 mm
phi_c=0.464733...
k_c,normal=23.6688619082 W/(m*K)
rho_c=3904.37584444 kg/m^3
cp_c=150.136452591 J/(kg*K)
```

## 与中央去球组合

Central Balls 是“增加一套中心子阵列”，Depopulated Center 是“从 main array 删除中央
矩形”，两者不是互斥的同一字段。高可信生成顺序应为：

1. 生成/裁剪 main array；
2. 生成 central array；
3. 对完全重合的离散位置去重，或对等效区域建立不重叠的布尔分区。

单变量等效样本中的 center block 与满包络 main block 平面上重叠；FloXML 证明 PACK 会
输出这两个对象，但不能据此推断求解器对重叠材料的优先级。PackStudio 应通过组合约束或
布尔分区消除含糊重叠。

## 证据

- `../templates/chip_array/xml_variations/option_switches/opt_v2_c005_centralballs_true/`
- `../templates/cbga_fc/xml_variations/option_switches/opt_v2_c006_centralballs_true/`
- `../templates/pbga_fc/xml_variations/option_switches/opt_v2_c006_centralballs_true/`
- `../templates/pbga_wb/xml_variations/option_switches/opt_v2_c006_centralballs_true/`
