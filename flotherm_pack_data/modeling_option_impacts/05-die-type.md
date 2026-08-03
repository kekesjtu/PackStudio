# Die Type：Actual Die / Thermal Die

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `new_package.dieType` |
| 值 | `actualDie` / `thermalDie` |
| 模板 | FBGA/FSBGA、QFP、SOIC、Wirebond PBGA |
| 默认 | `actualDie` |
| 证据 | 已验证；固定 8 根规则为精确反算 |

## 直接观察

该选项不改变 silicon die 的尺寸、位置、材料、DieSource 或监控点。FBGA、QFP 和
Wirebond PBGA 中只有两套 bondwire 等效材料的密度、比热和方向导热率变化；SOIC 的
默认实际焊线数就是 8，所以两个 FloXML 字节级相同。

## 精确公式

PACK 的 bondwire 高导热方向符合：

```text
k_high = k_mold + phi_wire * (k_gold - k_mold)
phi_wire proportional to N_wire
```

当前材料常数可反算为：

```text
k_mold = 0.68 W/(m*K)
k_gold = 296 W/(m*K)
rho_gold = 19300 kg/m^3
cp_gold = 132 J/(kg*K)
```

比较 `(k_actual - 0.68)/(k_thermal - 0.68)`：

| 模板 | Actual 高向 k | Thermal 高向 k | 比例 | 数量解释 |
|---|---:|---:|---:|---|
| FBGA | 30.8810137519 | 10.3443244006 | 3.125 | 25 / 8 |
| QFP | 54.8883051392 | 14.2320762848 | 4 | 32 / 8 |
| Wirebond PBGA | 47.4553300989 | 3.77258380819 | 15.125 | 121 / 8 |
| SOIC | 11.2952762295 | 相同 | 1 | 8 / 8 |

因此当前默认模型中：

```text
N_effective(actualDie)  = 实际配置焊线数
N_effective(thermalDie) = 8
```

几何块不增删，因为焊线数量已压缩进等效材料体积分数。

## PackStudio 结论

应把 Die Type 实现成 bondwire 数量策略，而不是替换 silicon die。若不需要 thermal-test
die 语义，可默认 `actualDie`；若保留选项，应复用同一焊线均质公式。

## 证据

- `../templates/fbga_fsbga/xml_variations/option_switches/opt_v2_c002_dietype_thermaldie/`
- `../templates/qfp_family/xml_variations/option_switches/opt_v2_c004_dietype_thermaldie/`
- `../templates/soic_family/xml_variations/option_switches/opt_v2_c005_dietype_thermaldie/`
- `../templates/wirebond_pbga/xml_variations/option_switches/opt_v2_c002_dietype_thermaldie/`
