# Flip-chip Bump Array Type

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `flipChipBumps.arrayType` |
| 值 | `nonRegularArray` / `regularArray` |
| 模板 | Flip-chip CBGA、Flip-chip PBGA |
| 默认 | `nonRegularArray` |

## 建模影响

两种模式都只导出同一个 `fc_bumps` 均质 cuboid；差别是用于材料均质的 bump 数量来源：

```text
nonRegularArray: N = totalNumberOfBumps_MNC4
regularArray:    N = Nx * Ny
```

验证分支给 regular array 初始化 `Nx=6, Ny=6`，所以 N 从 49 变为 36。包络和 bump
直径保持 `1.8 × 1.8 mm`、`0.12 mm`：

```text
phi_regular = 36 * pi * 0.12^2 / (4 * 1.8^2)
            = 0.1256637061435917
```

以 Pb90/Sn10 和 underfill 为组分：

```text
k = phi_regular*36 + (1-phi_regular)*0.6
  = 5.048495197483146
rho = 1351.7591773374672
cp = 141.90879927467805
```

与导出 `Bumps` 材料完全一致。

## 数据边界

Non-Regular 的具体 bump map 未导出为离散几何；当前只知道总数。Regular 模式能由 Nx、
Ny 精确计算。PackStudio 当前产品决策固定采用规则全阵列，不复刻复杂 bump map。

## 证据

- `../templates/flip_chip_cbga/xml_variations/option_switches/opt_v2_c005_arraytype_regulararray/`
- `../templates/flip_chip_pbga/xml_variations/option_switches/opt_v2_c005_arraytype_regulararray/`
