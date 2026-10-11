# Model Thermal Vias As

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `modelingOptions.modelThermalViasAs` |
| 值 | `discreteCuboids` / `isotropicCuboid` / `orthotropicCuboid` |
| 模板 | Wirebond PBGA |
| 默认 | `discreteCuboids` |

## Discrete Cuboids

输出 5×5 个 via，基准 `d=0.25 mm`、`p=1.27 mm`、`h=0.324 mm`、镀层
`t=0.025 mm`。铜环截面比例为：

```text
phi_Cu_shell = 1 - ((d-2t)/d)^2 = 0.36
```

孔芯按无质量、无导热占位处理，所以离散 `Via` 材料为：

```text
k_via=0.36*385=138.6 W/(m*K)
rho_via=0.36*8930=3214.8 kg/m^3
cp_via=385 J/(kg*K)
```

## 阵列等效块

Isotropic 和 Orthotropic 都用一个 5.33×5.33×0.324 mm 的 `thermal_via` 替换 25 个
离散块：

```text
L = (5-1)*1.27 + 0.25 = 5.33 mm
phi_via = 25*pi*0.25^2/(4*5.33^2)
        = 0.04319718927197
```

基体是 BT (`k=0.2`、`rho=1900`、`cp=921`)。共同结果：

```text
k_normal = phi_via*138.6 + (1-phi_via)*0.2
         = 6.178490995240862 W/(m*K)
rho_eff  = phi_via*3214.8 + (1-phi_via)*1900
         = 1956.795664454788 kg/m^3
cp_eff   = (phi_via*3214.8*385
           +(1-phi_via)*1900*921) / rho_eff
         = 882.961028913521 J/(kg*K)
```

两种等效模式的唯一区别是方向性：

| 模式 | kx=ky | kz |
|---|---:|---:|
| isotropicCuboid | 6.17849099524 | 6.17849099524 |
| orthotropicCuboid | 0.2 | 6.17849099524 |

因此 isotropic 会把 via 的强 z 向通道错误地复制到平面方向；orthotropic 才保留“基板
平面导热由 BT 控制、法向由 via 增强”的假设。

## PackStudio 取舍

这不是 BGA solder-ball array 层。项目当前限制“只有 BGA array 层提供离散/各向异性
选择”时，thermal via 可固定为一个经验证的表达，不必照搬三个 UI 选项；若保留等效块，
优先使用 orthotropic 公式。

## 证据

- `../templates/pbga_wb/xml_variations/option_switches/opt_v2_c006_modelthermalviasas_isotropiccuboid/`
- `../templates/pbga_wb/xml_variations/option_switches/opt_v2_c007_modelthermalviasas_orthotropiccuboid/`
- 基准：`../templates/pbga_wb/baseline/model.xml`
