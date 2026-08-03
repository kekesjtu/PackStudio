# Grid Density

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `modelingOptions.gridDensity` |
| 值 | `fine` / `medium` / `coarse` |
| 模板 | 全部 8 类模板 |
| 默认 | `fine` |

该选项只改变 `keypoint` 与 `keypoint_z` 的 grid constraints；几何、材料和物理边界不变。

## Fine 与 Medium

两种模式都使用：

```text
enable_min_cell_size = true
min_cell_size = 2e-6 m
number_cells_control = max_size
```

同一个 `max_size` 同时写入 constraint 本身及其 low/high inflation。由 8 类模板精确反算：

```text
fine:
  max_size_xy = Sxy/20
  max_size_z  = Sz_high_inflation/20

medium:
  max_size_xy = Sxy/10
  max_size_z  = Sz_high_inflation/12
```

`Sxy` 是模型全部几何的最大横向 span；`Sz_high_inflation` 是 PACK 为 z 高侧设置的
`inflation_size`，不一定等于封装本体高度。low/high inflation 的 type、percent/size 和
inflation extent 在 Fine→Medium 时不变。

## 各模板精确输出

单位均为 mm：

| 模板 | Fine XY | Medium XY | Fine Z | Medium Z |
|---|---:|---:|---:|---:|
| Bare Die | 0.245 | 0.490 | 0.022 | 0.036666667 |
| FBGA/FSBGA | 0.200 | 0.400 | 0.141 | 0.235 |
| Flip-chip CBGA | 0.300 | 0.600 | 0.226 | 0.376666667 |
| Flip-chip PBGA | 0.300 | 0.600 | 0.226 | 0.376666667 |
| QFN | 0.600 | 1.200 | 0.090 | 0.150 |
| QFP | 0.450 | 0.900 | 0.150 | 0.250 |
| SOIC | 0.300 | 0.600 | 0.162 | 0.270 |
| Wirebond PBGA | 0.750 | 1.500 | 0.176 | 0.293333333 |

例如 Bare Die 的 `Sxy=4.9 mm`，z high inflation size 为 0.44 mm：

```text
fine:   4.9/20=0.245, 0.44/20=0.022
medium: 4.9/10=0.490, 0.44/12=0.036666667
```

## Coarse

Coarse 不给出较大的 `max_size`，而是对两个 constraint 及其 low/high inflation 全部执行：

```text
number_cells_control: max_size -> min_number
remove max_size
min_number = 1
```

`enable_min_cell_size=true` 和 `min_cell_size=2 µm` 保留，inflation 类型与范围也保留。
所以 Coarse 的准确含义是“每段至少一个 cell，由网格器决定实际尺寸”，不是 Fine 的固定
2×或 4×缩放；无法预先给出固定总单元数。

## 生成顺序

`Sxy` 和 z inflation size 会随 outline、top cover、substrate layer、exposed pad 等几何改变。
正确流程是先完成全部几何和 grid region，再根据 density 写 constraints；不能缓存模板
基准表中的绝对 max size。

## 证据

- 各模板 `../templates/<template>/baseline/model.xml`
- 各模板 `../templates/<template>/xml_variations/option_switches/*griddensity_medium/`
- 各模板 `../templates/<template>/xml_variations/option_switches/*griddensity_coarse/`
