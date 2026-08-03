# Underfill

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `flipChipBumps.underfill` |
| 值 | `true` / `false` |
| 模板 | Flip-chip CBGA、Flip-chip PBGA |
| 默认 | `true` |

## 建模影响

PACK 始终只导出一个 `fc_bumps` cuboid，不导出独立 bumps 和 underfill 几何。开关只改变
该 cuboid 的均质材料；几何 `1.8 × 1.8 × 0.1 mm` 保持不变。

默认组分：

```text
C4 solder: Pb90/Sn10
rho = 10750, cp = 142, k = 36

underfill:
rho = 1, cp = 1, k = 0.6

air:
rho = 1.1614, cp = 1007, k = 0.0261
```

49 个直径 `d=0.12 mm` 的 bump 位于 `1.8 × 1.8 mm` 包络内：

```text
phi_bump = 49 * pi * 0.12^2 / (4 * 1.8^2)
         = 0.17104226669544428
```

### Underfill = true

```text
k = phi_bump * 36 + (1-phi_bump) * 0.6
  = 6.654896241018727

rho = phi_bump * 10750 + (1-phi_bump) * 1
    = 1839.5333247093304

cp = [phi_bump*10750*142 + (1-phi_bump)*1*1] / rho
   = 141.93646049309032
```

### Underfill = false

矩阵由 underfill 换成静止空气：

```text
k = phi_bump * 36 + (1-phi_bump) * 0.0261
  = 6.179157397875242
rho = 1839.6671184874856
cp = 142.45267975333368
```

上述结果与两类模板 FloXML 逐位一致。

## PackStudio 取舍

PACK 参考输出是各向同性材料。依据项目决策，PackStudio 的 bumps+underfill 应始终生成
有真实厚度的正交各向异性等效层，不提供 PACK 的 isotropic/collapsed 两种选择。本文件
的体积分数、密度和比热仍可复用；方向导热率采用 PackStudio 专用推导。

## 证据

- `../materials/materials_manual_captured.json`
- `../templates/flip_chip_cbga/baseline/model.xml`
- `../templates/flip_chip_cbga/xml_variations/option_switches/opt_v2_c002_underfill_false/`
