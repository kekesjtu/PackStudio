# Bond Wire Modeling

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `modelingOptions.bondWireModeling` |
| 值 | `include` / `ignore` |
| 模板 | FBGA/FSBGA |
| 默认 | `include` |

## 建模影响

`include` 不逐根建立圆柱 wire，而是在 die 四周生成 8 个矩形等效块：四个水平段和四个
竖直段。两个 orthotropic 材料 `bondwire1`、`bondwire2` 分别表达 x、y 主方向的导热。

`ignore` 会同时删除：

- 整个 `BondWires` assembly；
- `bw_h_*`、`bw_v_*` 共 8 个 cuboid；
- `bondwire1`、`bondwire2` 两种材料。

die、encapsulant、source、monitor 和其他封装几何均不变。也就是说，该选项不是把
bondwire 材料换成低导热树脂，而是让等效块不存在，原位置由外层 encapsulant 覆盖。

## 热学后果

忽略 bond wires 会移除 die 顶部/边缘到 substrate trace 的并联金属热通路，并减少对应的
金属热容。影响大小与 wire 数量、直径和长度有关；不存在一个可在删除后补偿的固定接触
热阻。

若实现 include，材料公式和方向定义见 [Model Bond Wires As](26-model-bond-wires-as.md)，
计数来源见 [Number of Bond Wires equals Solder Balls](25-bond-wire-count-mode.md)。

## 证据

- `../templates/chip_array/xml_variations/option_switches/opt_v2_c007_bondwiremodeling_ignore/`
- 基准：`../templates/chip_array/baseline/model.xml`
