# Model Tie Bars As

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `modelingOptions.modelTieBarsAs` |
| 值 | `accurate` / `approximate` |
| 模板 | QFP |
| 默认 | `accurate` |

## Accurate

输出两个 assembly：

- `tie_bars`：四个水平、四个竖直金属等效块，厚 0.15 mm；
- `tiebar_plt`：与之同平面的 8 个 collapsed epoxy partner 块，名义厚 0.42 mm。

金属块横向宽度为 0.50 mm。`tie_bar1/2` 是 biaxial 材料：

```text
rho=8900 kg/m^3
cp=385 J/(kg*K)
k_in_plane=106.596347263872 W/(m*K)
k_normal=0.68 W/(m*K)
```

高导热率与默认 leadframe 金属 `k_metal=301.5` 的关系精确为：

```text
k_in_plane = k_metal/(2*sqrt(2))
           = 106.596347263872
```

这很可能是在轴对齐矩形中折算斜向 tie-bar 路径；这是强推断，PACK 未公开推导。

## Approximate

块数量不变，但横向宽度从 `w_accurate=0.50 mm` 缩至 `w_approx=0.42 mm`，靠外侧的
起点相应移动以保持另一边界。材料由 biaxial 改为 isotropic，并按：

```text
r = w_accurate/w_approx = 0.50/0.42 = 25/21
k_approx   = r*k_in_plane = 126.900413409371
rho_approx = r*8900       = 10595.2380952381
cp_approx  = r*385        = 458.333333333333
```

`k*w` 和 `rho*w` 因而保持不变；但是 `rho*cp*w` 不保持不变，因为 PACK 也把比热乘了
`r`。这不是通常的能量守恒均质公式，而是导出中可重复观察到的算法，复刻兼容模式应照录，
物理改进模式则应另立决策并测试。

## 方向差异

Approximate 的 isotropic `k=126.9004` 同时应用于 z；相较 Accurate 的
`k_normal=0.68`，法向导热会被大幅提高。该选项同时改变几何宽度、材料数值和方向性，
不能只实现为“低精度网格”。

## 证据

- `../templates/pqfp/xml_variations/option_switches/opt_v2_c008_modeltiebarsas_approximate/`
- 基准：`../templates/pqfp/baseline/model.xml`
