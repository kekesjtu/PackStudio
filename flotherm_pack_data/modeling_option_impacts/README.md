# FloTHERM PACK 重要选项对建模的影响

本目录以“一项 UI 选项一个文件”的方式，说明当前 FloTHERM PACK 2504 参考数据中
重要布尔、枚举、结构及建模选项对 FloXML 的影响。39 份选项文件覆盖 42 个内部
option 目标和 132 个单变量导出案例；同一 UI 语义在不同模板中的内部属性差异会在
同一文件内分别列出。

## 使用边界

- 本目录说明的是 **PACK 参考行为**，不是 PackStudio 已承诺实现的功能清单。
- JEDEC 的不同内部属性合并为一个 `JEDEC Footprint` 文件；具体预设是查表，不是公式。
- 材料下拉框和连续数值字段不按每个候选值拆文件；当 option 触发材料均质时，会给出
  所需组分和精确公式。
- `Solder Ball Map`、交错阵列以及 PACK 的 collapsed bumps 等参考行为，会明确标注为
  PackStudio 当前产品决策不采用。
- FloXML 使用 SI 单位；文档中的几何示例统一换算为 mm。

## 证据等级

| 等级 | 含义 |
|---|---|
| 已验证 | 单变量 FloSCRIPT 已回放，FloXML 差异可直接观察 |
| 精确反算 | 公式结果与导出值在双精度误差内一致 |
| 强推断 | 多个独立案例符合相同规则，但 PACK 没有公开内部公式 |
| 数据边界 | 缺少依赖初始化、编辑器内容或非默认材料，不能解释为完整物理模型 |

## 通用等效公式

以下符号在各文件中复用。组分体积分数为 `phi_i`：

```text
sum(phi_i) = 1
rho_eff = sum(phi_i * rho_i)
cp_eff  = sum(phi_i * rho_i * cp_i) / rho_eff
```

与主要热流方向并联的导热率使用算术混合：

```text
k_parallel = sum(phi_i * k_i)
```

PACK 对竖直球、bump、via 阵列的正交/双轴等效通常采用：

```text
k_normal   = k_parallel
k_in_plane = k_matrix
```

规则阵列包络和圆柱到等面积正方形的常用公式：

```text
Lx = (Nx - 1) * px + d
Ly = (Ny - 1) * py + d
s_equal_area = d * sqrt(pi) / 2
phi = Nx * Ny * pi * d^2 / (4 * Lx * Ly)
```

参考数据反算采用的静止空气属性：

```text
rho_air = 1.1614 kg/m^3
cp_air  = 1007 J/(kg*K)
k_air   = 0.0261 W/(m*K)
```

## 选项索引

### 初始化与芯片

1. [Outline Type](01-outline-type.md)
2. [JEDEC Footprint](02-jedec-footprint.md)
3. [PQFP Package Type](03-pqfp-package-type.md)
4. [SOP Package Type](04-sop-package-type.md)
5. [Die Type](05-die-type.md)
6. [Exposed Pad](06-exposed-pad.md)
7. [Flipped Die](07-flipped-die.md)
8. [Non-uniform Die Heat](08-non-uniform-die-heat.md)

### Flip-chip 顶部结构与 bumps

9. [Top Cover](09-top-cover.md)
10. [Underfill](10-underfill.md)
11. [Flip-chip Bump Array Type](11-flip-chip-bump-array-type.md)
12. [Model Flip Chip Bumps As](12-model-flip-chip-bumps-as.md)
13. [Include Slug](13-include-slug.md)
14. [Adhesive Present Under Slug Foot](14-adhesive-under-slug-foot.md)
15. [Enable Die Flush](15-enable-die-flush.md)
16. [Stiffener](16-stiffener.md)
17. [Include Backside Spreader](17-include-backside-spreader.md)

### 基板、vias、焊线与 leadframe

18. [Substrate Layer](18-substrate-layer.md)
19. [Filled Vias](19-filled-vias.md)
20. [FBGA Via Modeling](20-via-modeling.md)
21. [Model Core Vias As](21-model-core-vias-as.md)
22. [Model Thermal Vias As](22-model-thermal-vias-as.md)
23. [QFN Model Vias As](23-model-vias-as-qfn.md)
24. [Bond Wire Modeling](24-bond-wire-modeling.md)
25. [Number of Bond Wires equals Solder Balls](25-bond-wire-count-mode.md)
26. [Model Bond Wires As](26-model-bond-wires-as.md)
27. [Model Lead Frames As](27-model-lead-frame-as.md)
28. [User Defined Leadframe Coverage](28-user-defined-leadframe-coverage.md)
29. [Model Tie Bars As](29-model-tie-bars-as.md)
30. [Model Leads and Solder Interconnect As](30-model-leads-and-solder-interconnect-as.md)

### 焊球排布与外部热路径

31. [Model Solder Ball Array As](31-model-solder-ball-array-as.md)
32. [Solder Ball Map](32-solder-ball-map.md)
33. [Solder Ball Staggered Matrix](33-solder-ball-staggered-matrix.md)
34. [Depopulated Center](34-depopulated-center.md)
35. [Central Balls](35-central-balls.md)
36. [Central Balls Staggered Matrix](36-central-balls-staggered-matrix.md)
37. [Include Thermal Land and Solder](37-include-thermal-land-and-solder.md)

### 网格

38. [Localize Grid](38-localize-grid.md)
39. [Grid Density](39-grid-density.md)

## 主要证据入口

- `../templates/<template>/ui.json`：UI 值域、默认值和条件依赖。
- `../templates/<template>/baseline/params.json`：基准输入。
- `../templates/<template>/baseline/model.xml`：基准 FloXML。
- `../templates/<template>/xml_variations/option_switches/`：单 option 脚本、输出与差异。
- `../parameter_coverage.json`：覆盖策略和分支基线。
- `../validation/report.json`：全量验收结果。
