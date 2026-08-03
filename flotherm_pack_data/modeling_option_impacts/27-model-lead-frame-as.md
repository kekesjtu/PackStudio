# Model Lead Frames As

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `modelingOptions.modelLeadFrameAs` |
| 值 | `orthotropicCuboid` / `isotropicCuboid` |
| 模板 | QFP |
| 默认 | `orthotropicCuboid` |

## 建模影响

几何完全不变；方向材料 `LeadFrame_1x/1y/2x/2y` 在 isotropic 模式下合并为
`LeadFrame_1` 和 `LeadFrame_2`。所有 lead cuboid 只改材料引用。

### Orthotropic

| 区域 | 沿 lead 与 z | 横向 |
|---|---:|---:|
| LeadFrame_1，mold 内 | 151.09 | 0.68 |
| LeadFrame_2，body 外 | 150.76305 | 0.0261 |

### Isotropic

```text
LeadFrame_1: kx=ky=kz=151.09 W/(m*K)
LeadFrame_2: kx=ky=kz=150.76305 W/(m*K)
```

密度和比热不变。

## 默认覆盖率公式

基准 lead 宽 `B=0.4 mm`、pitch `e=0.8 mm`，所以金属覆盖率 `c=B/e=0.5`。
leadframe 金属 Cu-EFTEC-64T 为 `rho=8900`、`cp=385`、`k=301.5`。

mold 内区域：

```text
k_high = c*301.5 + (1-c)*0.68 = 151.09
k_low  = 0.68
rho    = c*8900 + (1-c)*1820 = 5360
cp     = (c*8900*385 + (1-c)*1820*882) / 5360
       = 469.378731343
```

body 外区域以空气为基体：

```text
k_high = c*301.5 + (1-c)*0.0261 = 150.76305
k_low  = 0.0261
rho    = c*8900 + (1-c)*1.1614 = 4450.5807
cp     = (c*8900*385 + (1-c)*1.1614*1007) / rho
       = 385.081156915
```

## 取舍

Isotropic 保留轴向等效导热，却把横向树脂/空气通道提升约 222 倍/5776 倍。因此它适合
减少方向材料数量，不适合高可信的横向热扩散表达。

## 证据

- `../templates/qfp_family/xml_variations/option_switches/opt_v2_c006_modelleadframeas_isotropiccuboid/`
- 基准：`../templates/qfp_family/baseline/model.xml`
