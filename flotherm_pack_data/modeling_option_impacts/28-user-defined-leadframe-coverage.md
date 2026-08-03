# User Defined Leadframe Coverage

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `leadFrame.userDefinedLeadframeCoverage` |
| 值 | `noDefaultIsBe` / `yes` |
| 模板 | QFP、SOIC |
| 默认 | `noDefaultIsBe` |

`noDefaultIsBe` 的 UI 标签是 “No. The default coverage is B/e”。当选择 yes 时，使用
`leadFrame.leadframeCoveragePercentage/100`。

```text
c = B/e                                      if noDefaultIsBe
c = leadframeCoveragePercentage/100          if yes
```

## 建模影响

lead cuboid 几何和数量不变；只重算封装 body 内部的 leadframe 等效材料。沿 lead 的方向与
z 使用金属/树脂并联值，横向保持树脂值：

```text
k_high = c*k_metal + (1-c)*k_mold
k_low  = k_mold
rho    = c*rho_metal + (1-c)*rho_mold
cp     = (c*rho_metal*cp_metal
         +(1-c)*rho_mold*cp_mold) / rho
```

## QFP 精确结果

`B/e=0.4/0.8=0.5`；用户分支为 40%。金属 Cu-EFTEC-64T
(`rho=8900, cp=385, k=301.5`)，mold (`rho=1820, cp=882, k=0.68`)：

| c | k_high | rho | cp |
|---:|---:|---:|---:|
| 0.5 | 151.09 | 5360 | 469.378731343 |
| 0.4 | 121.008 | 4652 | 501.664660361 |

只改变 `LeadFrame_1x/1y`；body 外以空气为基体的 `LeadFrame_2x/2y` 不变。

## SOIC 精确结果

`B/e=0.4/1.27=0.314960629921`；用户分支为 40%。当前材料库输出为：

```text
Cu-CDA-194: rho=8800, cp=1,   k=263
EPOXY:      rho=1820, cp=882, k=0.68
```

| c | k | rho | cp |
|---:|---:|---:|---:|
| 0.314960629921 | 83.3004724409 | 4018.42519685 | 274.342359995 |
| 0.4 | 105.608 | 4612 | 209.597571552 |

SOIC 的 `LeadFrame_1` 在该模板中是 isotropic，因此同一个 `k` 写入三方向。`cp=1` 是
当前 FloTHERM PACK 材料记录的实际导出值，明显不像常见铜合金物性；复刻应忠实读材料
库，产品默认库则应单独审校，不能把这个数当成通用常数。

## 证据

- `../templates/qfp_family/xml_variations/option_switches/opt_v2_c005_userdefinedleadframecoverage_yes/`
- `../templates/soic_family/xml_variations/option_switches/opt_v2_c006_userdefinedleadframecoverage_yes/`
