# BGA 与 Bumps 建模表达

BGA 下拉框参照 PACK 的 `Model Solder Ball Array As`，按家族提供以下表达。

| 封装                | 选项                                                                                                                       |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Chip Array          | Discrete Cuboids                                                                                                           |
| Flip Chip CBGA/PBGA | Orthotropic Cuboid、Discrete Cuboids                                                                                       |
| Wirebond PBGA       | Isotropic Cuboid、Discrete Cuboids、Orthotropic Cuboid（ Isotropic Cuboid 使用焊料与空气的轴向并联混合值作为三向导热率。） |

启用显式去球或 Solder Ball Map 时，BGA 焊球必须使用离散表达，与名单是否为空无关。桌面在启用或打开这类方案时，建模方式按需自动切换为 Discrete Cuboids（`discrete`），在字段旁持续提示，并锁定建模方式；两项均关闭后恢复选择能力，保留当前建模方式。直接提交给 Core 的矛盾输入通过统一的前校验报告，不在生成过程中修改参数。

显式去球通过独立的业务开关启用，不依赖“主阵列中心去球”开关；启用且名单非空时，主阵列按显式名单确定保留单元。关闭显式去球后名单保留，但不参与建模、数量计算和校验。焊球坐标表仅在勾选使用时显示并参与建模与校验，关闭时保留坐标数据。

Bumps 采用有厚度的各向同性等效层。凸点的建模选项下拉框仅展示 `Isotropic Cuboid`。FC 的 Bumps 不使用底填时基体为空气。
