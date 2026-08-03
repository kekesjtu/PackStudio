# Enable Die Flush

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `topCover.enableDieFlush` |
| 值 | `false` / `true` |
| 模板 | Flip-chip CBGA、Flip-chip PBGA |
| 前提 | `topCover=encapsulant` |

## 建模影响

该选项不移动 die，也不改变材料。它降低 encapsulant 顶面，使 die 顶面与封装顶部齐平，
并同步移动 CaseTemp、`z_top` 和 z 网格包络。

验证案例：

```text
t_encapsulant: 1.20 -> 0.71 mm
CaseTemp.z:     2.7225 -> 2.2374 mm
z_top:          2.75 -> 2.26 mm
```

几何规则为：

```text
z_encap_top_flush = z_die_top + numerical_clearance
t_encap_flush = z_encap_top_flush - z_encap_bottom
```

当前输出的顶面比名义 die top 保留约 0.01 mm 的数值/封装余量；该余量来自 PACK 内部
规则，不应从单一样本泛化为所有封装的固定常数。

## 证据

- `../templates/flip_chip_cbga/xml_variations/option_switches/opt_v2_c011_enabledieflush_true/`
- `../templates/flip_chip_pbga/xml_variations/option_switches/opt_v2_c010_enabledieflush_true/`
