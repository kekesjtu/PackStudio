# FBGA Via Modeling

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `modelingOptions.viaModeling` |
| 值 | `accurate` / `approximate` |
| 模板 | FBGA/FSBGA |
| 默认 | `accurate` |

## 共同点

两种模式都输出 5×5、共 25 个 isotropic via cuboid，高度均为 0.324 mm。因此
`approximate` 不是把阵列合成一个大块，而是降低每个块所表达的空间细节。

## Accurate

- via 截面按外径圆的等面积正方形生成；
- via 中心按独立 via pitch 和 `viaOffsetX/Y` 放置；
- 材料是镀铜环与空气孔芯的均质材料。

基准中 `d_v=0.20 mm`：

```text
s_accurate = d_v*sqrt(pi)/2 = 0.177245385091 mm
```

`Via` 材料为 `rho=3907.5282875`、`cp=385.103990245`、
`k=168.45218125`，推导见 [Filled Vias](19-filled-vias.md)。

## Approximate

- 仍输出 25 个块；
- 每个 via 扩大为对应 solder-ball 的等面积正方形足迹；
- 中心改为与 solder-ball 中心对齐，忽略基准中的 0.4 mm via offset；
- 为保持铜/via 总量，再把 accurate `Via` 与 BT 在扩大块内二次均质。

基准 solder-ball 外径 `d_b=0.46 mm`：

```text
s_approx = d_b*sqrt(pi)/2 = 0.407664385708 mm
phi_via  = s_accurate^2 / s_approx^2
         = (d_v/d_b)^2
         = 0.189035916824
```

以 `Via_accurate` 和 BT 为两组分：

```text
k_approx   = phi_via*k_via + (1-phi_via)*k_BT
rho_approx = phi_via*rho_via + (1-phi_via)*rho_BT
cp_approx  = (phi_via*rho_via*cp_via
             +(1-phi_via)*rho_BT*cp_BT) / rho_approx
```

精确结果：

```text
k_approx   = 32.00570534026464 W/(m*K)
rho_approx = 2279.4949503780717 kg/m^3
cp_approx  = 747.3445780986646 J/(kg*K)
```

## 物理含义与取舍

Approximate 保持总体积热容和 z 向并联导热能力，但丢失 via 相对焊球的偏移以及小截面局部
温度梯度。扩大块可减少相邻几何特征造成的网格关键点；它不等同于“更粗的纯铜 via”。

## 证据

- `../templates/chip_array/xml_variations/option_switches/opt_v2_c006_viamodeling_approximate/`
- 基准：`../templates/chip_array/baseline/model.xml`
