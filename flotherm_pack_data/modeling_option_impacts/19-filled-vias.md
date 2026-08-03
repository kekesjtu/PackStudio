# Filled Vias

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `vias.filledVias` |
| 值 | `no` / `yes` |
| 模板 | FBGA/FSBGA |
| 默认 | `no` |

## 建模影响

该选项只改变 25 个离散 via 共用的 `Via` 材料；via 数量、等面积正方形截面、位置和高度
完全不变。

- `no`：铜镀层与空气孔芯的均质材料；
- `yes`：整个外径截面按纯铜处理。

## 镀层体积分数

外径 `d`、镀层厚度 `t`，假设镀层形成同心圆环：

```text
phi_Cu = [pi*d^2/4 - pi*(d-2t)^2/4] / [pi*d^2/4]
       = 1 - ((d-2t)/d)^2
phi_core = 1 - phi_Cu
```

未填充 via 的材料为：

```text
k_via   = phi_Cu*k_Cu + phi_core*k_air
rho_via = phi_Cu*rho_Cu + phi_core*rho_air
cp_via  = (phi_Cu*rho_Cu*cp_Cu + phi_core*rho_air*cp_air) / rho_via
```

基准 `d=0.20 mm`、`t=0.025 mm`，所以 `phi_Cu=0.4375`。精确结果：

| 状态 | rho (kg/m³) | cp (J/(kg·K)) | k (W/(m·K)) |
|---|---:|---:|---:|
| no | 3907.5282875 | 385.103990245 | 168.45218125 |
| yes | 8930 | 385 | 385 |

离散 via 的正方形边长仍按外径等面积转换：

```text
s = d*sqrt(pi)/2 = 0.177245385091 mm
```

## 解释边界

`yes` 在当前导出中等价于“铜填充”，而不是用另一个可配置填料填充。若 PackStudio 将来
支持树脂填孔，应扩展为三组分公式，不能复用这里的纯铜结果。

## 证据

- `../templates/fbga_fsbga/xml_variations/option_switches/opt_v2_c005_filledvias_yes/`
- 基准：`../templates/fbga_fsbga/baseline/model.xml`
