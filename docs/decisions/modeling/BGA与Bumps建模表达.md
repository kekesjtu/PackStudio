# BGA 与 Bumps 建模表达

BGA 下拉框参照 PACK 的 `Model Solder Ball Array As`，按家族提供以下表达。

| 封装                | 选项                                                                                                                       |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Chip Array          | Discrete Cuboids                                                                                                           |
| Flip Chip CBGA/PBGA | Orthotropic Cuboid、Discrete Cuboids                                                                                       |
| Wirebond PBGA       | Isotropic Cuboid、Discrete Cuboids、Orthotropic Cuboid（ Isotropic Cuboid 使用焊料与空气的轴向并联混合值作为三向导热率。） |

使用显式去球和 Solder Ball Map 时，BGA 焊球必须使用离散表达。桌面中展开显式去球或勾选使用焊球坐标表时，建模方式按需自动切换为 Discrete Cuboids（`discrete`），并提示用户；收起或关闭后保留当前建模方式。

显式去球名单独立于“主阵列中心去球”开关生效；名单非空时主阵列按显式名单确定保留单元。焊球坐标表仅在勾选使用时显示并参与建模与校验，关闭时保留坐标数据。

Bumps 采用有厚度的各向同性等效层。凸点的建模选项下拉框仅展示 `Isotropic Cuboid`。FC 的 Bumps 不使用底填时基体为空气。
