# QFN Model Vias As

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `vias.modelViasAs` |
| 值 | `ignored` / `discrete` / `lumped` |
| 模板 | QFN |
| 默认 | `ignored` |

## 三种模式

| 值 | FloXML 几何 | 材料类型 |
|---|---|---|
| ignored | 不生成 Vias assembly | 无 |
| discrete | 5×5 个 via cuboid | isotropic `Via` |
| lumped | 一个阵列包络 cuboid | biaxial `Vias` |

选择 ignored 会完全切断 DAP 下方 vias 提供的板向热通路。

## Discrete

基准 `Nx=Ny=5`、`d=0.20 mm`、`p=0.50 mm`、`h=0.85 mm`、镀层
`t=0.020 mm`。铜环比例：

```text
phi_Cu_shell = 1 - ((d-2t)/d)^2 = 0.36
s_equal_area = d*sqrt(pi)/2 = 0.177245385091 mm
```

孔芯按无质量、无导热处理：

```text
k_via=0.36*385=138.6 W/(m*K)
rho_via=0.36*8930=3214.8 kg/m^3
cp_via=385 J/(kg*K)
```

## Lumped

阵列替换为 2.2×2.2×0.85 mm 的单块：

```text
L = (5-1)*0.50 + 0.20 = 2.20 mm
phi_via = 25*pi*0.20^2/(4*2.20^2)
        = 0.16227234780939
```

由导出值精确反算，基体为 `k=0.32 W/(m*K)`、`rho=1200 kg/m³`、
`cp=880 J/(kg*K)`。PACK 采用：

```text
k_in_plane = k_matrix = 0.32
k_normal   = phi_via*138.6 + (1-phi_via)*0.32
           = 22.7590202550825 W/(m*K)
rho_eff    = phi_via*3214.8 + (1-phi_via)*1200
           = 1526.946326366359 kg/m^3
cp_eff     = (phi_via*3214.8*385
             +(1-phi_via)*1200*880) / rho_eff
           = 710.885865671110 J/(kg*K)
```

基体属性是强推断：三项导出数值同时满足同一组分解，但 UI 并未给该基体命名。实现时应把
它作为明确的 QFN via-environment 默认材料，而不要误用空气或 BT。

## 证据

- `../templates/qfn/xml_variations/option_switches/opt_v2_c002_modelviasas_discrete/`
- `../templates/qfn/xml_variations/option_switches/opt_v2_c003_modelviasas_lumped/`
- 基准：`../templates/qfn/baseline/model.xml`
