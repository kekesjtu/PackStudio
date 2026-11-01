# BGA 与 Bumps 建模表达

## 决策

- BGA 焊球建模下拉框对应 PACK 的 `Model Solder Ball Array As`，选项文本采用 PACK 名称：`Discrete Cuboids`、`Orthotropic Cuboid`、`Isotropic Cuboid`。
- Chip Array 提供 `Discrete Cuboids`；Flip Chip CBGA/PBGA 提供 `Orthotropic Cuboid` 与 `Discrete Cuboids`。
- Wirebond PBGA 提供 `Isotropic Cuboid`、`Discrete Cuboids` 与 `Orthotropic Cuboid`。
- Bumps 采用有厚度的 Isotropic Cuboid 等效层。
- 凸点建模使用下拉框只展示 `Isotropic Cuboid`，对应 PACK 的 `Model Flip Chip Bumps As`（Bare Die 为 `Solder Bump Modeling`）；该选项仅声明表达方式，不参与几何生成。
- 建模与局部网格栏目按几何建模控件、局部网格开关和网格密度的顺序排列；凸点、焊球、通孔、键合线、引线框的建模方式控件集中在建模与局部网格栏目，局部网格开关与网格密度始终排在末尾。
- 建模方式下拉框的行标签沿用同栏目「…建模方式」中文写法，选项文本使用 PACK 英文枚举。

## 等效物性与几何规则

BGA 使用离散焊球与正交各向异性等效层；Wirebond PBGA 同时提供各向同性等效层，三向导热率取焊料与空气的轴向并联混合值。
等效层的密度按体积加权、比热按质量加权。显式去球和 Solder Ball Map 使用离散表达。
Bumps 使用有厚度的各向同性等效层，三方向导热率采用焊料与底填材料的并联混合值。
密度按体积加权，比热按质量加权。FC 的底填关闭分支使用空气作为基体。

## 依据与范围

依据为项目确认的 BGA 与 Bumps 建模表达范围。
本约定描述焊球和凸点的几何、等效物性表达。
