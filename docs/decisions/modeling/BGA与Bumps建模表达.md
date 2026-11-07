# BGA 与 Bumps 建模表达

BGA 下拉框参照 PACK 的 `Model Solder Ball Array As`，按家族提供以下表达。

| 封装                | 选项                                                                                                                       |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Chip Array          | Discrete Cuboids                                                                                                           |
| Flip Chip CBGA/PBGA | Orthotropic Cuboid、Discrete Cuboids                                                                                       |
| Wirebond PBGA       | Isotropic Cuboid、Discrete Cuboids、Orthotropic Cuboid（ Isotropic Cuboid 使用焊料与空气的轴向并联混合值作为三向导热率。） |

使用显式去球和 Solder Ball Map 时，BGA 焊球必须使用离散表达。

Bumps 采用有厚度的各向同性等效层。凸点的建模选项下拉框仅展示 `Isotropic Cuboid`。FC 的 Bumps 不使用底填时基体为空气。
