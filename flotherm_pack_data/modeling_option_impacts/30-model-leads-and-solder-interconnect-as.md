# Model Leads and Solder Interconnect As

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `modelingOptions.modelLeadAndSolderInterconnectAs` |
| 值 | `discreteLeads` / `orthotropicCuboid` |
| 模板 | QFN |
| 默认 | `discreteLeads` |

## 几何变化

基准每边 25 个 interconnect，四边共输出 100 个 solder 和 200 个上下 lead 段，即 300
个离散 cuboid。Orthotropic 模式将其替换为：

- 四个 `solder_*` 包络块；
- 四个 `leadtop_*` 包络块；
- 四个 `leadbot_*` 包络块。

总计 12 个块。每边阵列 span 为：

```text
L = (N-1)*pitch + b
  = (25-1)*0.4 + 0.2
  = 9.8 mm
```

金属/焊料在该 span 内的一维覆盖率：

```text
phi = N*b/L = 25*0.2/9.8 = 0.510204081632653
```

## Lead 等效材料

Cu-C19400 (`rho=8800, cp=1, k=260`) 与 EME-7730LF
(`rho=2010, cp=1, k=0.88`) 混合：

```text
k_high = phi*260 + (1-phi)*0.88
       = 133.084081632653 W/(m*K)
k_low  = 0.88 W/(m*K)
rho    = phi*8800 + (1-phi)*2010
       = 5474.285714285713 kg/m^3
cp     = 1 J/(kg*K)
```

## Solder 等效材料

Sn63/Pb37 (`rho=8400, cp=150, k=50.9`) 与空气混合：

```text
k_high = phi*50.9 + (1-phi)*0.0261
       = 25.9821714285714 W/(m*K)
k_low  = 0.0261 W/(m*K)
rho    = phi*8400 + (1-phi)*1.1614
       = 4286.283134693877 kg/m^3
cp     = (phi*8400*150 +(1-phi)*1.1614*1007) / rho
       = 150.113735737979 J/(kg*K)
```

沿该边 lead 排列/延伸的方向和 z 取 `k_high`，横向取 `k_low`；相邻两边使用 `Lead1/2`
及 `Solder1/2` 交换 x、y 主方向。

## 精度含义

该模式保留每边的总材料比例和轴向并联导热，但抹去 0.4 mm pitch 的局部冷热斑、单引脚
边界以及引脚之间的空气/树脂间隙。它是阵列均质，不是简单合并相邻矩形。

## 证据

- `../templates/qfn/xml_variations/option_switches/opt_v2_c004_modelleadandsolderinterconne_orthotropiccuboid/`
- 基准：`../templates/qfn/baseline/model.xml`
