# DES 字段与 PackStudio 内部参数对应表

供 PTA worktree 人工核对使用。对应范围为仓库内八类封装的原生 DES 样本、运行参数库和 C# 参数适配代码；此表描述字段语义与现有预设适配关系，不代表桌面程序提供 DES 导入/导出功能。

## 读取约定

- 原生保存的 `.des` 为 ZIP 容器，参数成员是 `键|值` 文本；原生预设源也可能直接保存为该文本。字段区分大小写，如 `b`、`bC4`、`td`、`tC4` 含义不同。
- 下表内部键默认指 `ProjectDocument.Values["键"]`；CLI 请求写作 `overrides["模板ID.键"]`。`Bga` 与 `Assignments` 单独列出。
- “原生属性”列表示 PACK 数据集的 `组件.属性`，嵌套结构补充子分支；`wizard.*` 表示新建向导属性。属性存在性与 PackStudio 是否配置预设绑定分开判断；未绑定的原生属性仍列出名称。`—（内部独立开关）` 表示在本机 PACK 2504 的完整数据集与向导属性清单中无一对一可编辑布尔属性。DES 列的 `—` 标明向导初始化或内部开关等无独立键的情况，具体原因见该行。
- 顶盖嵌套路径中的 lid/plate/encapsulant 用来区分子分支；FloSCRIPT 仍使用 name="topCover"，例如 stiffener 的 property_name="stiffener"，不把 topCover.lid 整段写入 name。
- 几何长度使用 mm，功率使用 W，覆盖率为 0–100 的百分数，数量为整数。原生表格解析中间值以 m 存储时，适配至内部表格须乘 1000。
- 对应必须结合模板与分支：`A2` 可以是基板厚度或塑封厚度，`MD/ME` 可以是焊球数或引脚数，`tda` 可以是芯片胶层或顶盖连接层。
- DES 缺键、空串、原生属性未指定、未启用组不是同一种状态。预设还经过原生向导初始化；不应把所有空串补 0，也不能只从 DES 文本复原所有预设值。

## 家族与方案标识

| DES 字段/来源 | 内部字段 | 对应规则 |
| --- | --- | --- |
| `package` | `TemplateId` | `Die`→`bare_die`；`QFN`→`qfn`；`tsop_conv`→`sop`；其余 `cbga_fc`、`pbga_fc`、`pbga_wb`、`chip_array`、`pqfp` 同名。 |
| `design` | `Name` | 语义对应方案名称；CLI 使用 `design_name`，并非由 DES 自动载入。 |
| 预设 ID / 源文件名 | `PresetId`、`Values["footprint.size"]` | DES 内容没有同名 footprint 字段；Bare Die 无原生预设绑定。 |
| `SummaryNotes`、`SummaryPartNumber`、`SummaryVendor` | — | 未暴露为方案字段；不映射到几何参数。 |

## 各封装参数

### bare_die

| DES 原始键 | PackStudio 内部键 | 含义 | 原生属性 / 数据来源 | 单位 / 转换 / 限制 |
| --- | --- | --- | --- | --- |
| `Ld` | `die.length` | 芯片长度 | `die.dieLengthLd` | mm；数值。原生数据集已确认；Bare Die 无运行预设绑定。 |
| `Wd` | `die.width` | 芯片宽度 | `die.dieWidthWd` | mm；数值。原生数据集已确认；Bare Die 无运行预设绑定。 |
| `td` | `die.thickness` | 芯片厚度 | `die.dieThicknessTd` | mm；数值。原生数据集已确认；Bare Die 无运行预设绑定。 |
| `P` | `die.power` | 芯片功率 | `die.packagePower` | W；数值。原生数据集已确认；Bare Die 无运行预设绑定。 |
| `flip` | `die.flipped` | 翻转芯片 | `die.flippedDie` | CHECKED→true；UNCHECKED→false。原生数据集已确认；Bare Die 无运行预设绑定。 |
| `bumped` | `bumps.enabled` | 包含凸点与底填充 | `bumpedDie.bumpedDie` | CHECKED→true；UNCHECKED→false。原生数据集已确认；Bare Die 无运行预设绑定。 |
| `nballs` | `bumps.total` | 凸点总数 | `bumpedDie.numberOfSolderBalls` | 整数计数。原生数据集已确认；Bare Die 无运行预设绑定。 |
| `b` | `bumps.diameter` | 凸点直径 | `bumpedDie.ballDiameterb` | mm；数值。原生数据集已确认；Bare Die 无运行预设绑定。 |
| `tsd` | `bumps.height` | 凸点层厚度 | `bumpedDie.ballHeight` | mm；数值。原生数据集已确认；Bare Die 无运行预设绑定。 |
| `localgrid` | `grid.enabled` | 局部网格 | `modelingOptions.localizeGrid` | CHECKED→true；UNCHECKED→false。原生数据集已确认；Bare Die 无运行预设绑定。 |
| `radio_lgc` | `grid.density` | 网格密度 | `modelingOptions.gridDensity` | 1→coarse；2→medium；3→fine。原生数据集已确认；Bare Die 无运行预设绑定。 |

### cbga_fc

| DES 原始键 | PackStudio 内部键 | 含义 | 原生属性 / 数据来源 | 单位 / 转换 / 限制 |
| --- | --- | --- | --- | --- |
| `—` | `footprint.size` | Footprint 尺寸（JEDEC） | `wizard.jedecFootprint` | 原生向导属性已确认；按家族/子类型选择。无独立 DES 键，内部保存为预设 ID。 |
| `D` | `substrate.length` | 基板长度 D | `packageSubstrate.substrateLengthD` | mm；数值。 |
| `E` | `substrate.width` | 基板宽度 E | `packageSubstrate.substrateWidthE` | mm；数值。 |
| `A2` | `substrate.thickness` | 基板厚度 A2 | `packageSubstrate.substrateThicknessA2` | mm；数值。 |
| `Ld` | `die.length` | 芯片长度 | `die.dieLengthLd` | mm；数值。 |
| `Wd` | `die.width` | 芯片宽度 | `die.dieWidthWd` | mm；数值。 |
| `td` | `die.thickness` | 芯片厚度 | `die.dieThicknessTd` | mm；数值。 |
| `P` | `die.power` | 芯片功率 | `die.packagePower` | W；数值。 |
| `MNC4` | `bumps.total` | 凸点总数 | `flipChipBumps.totalNumberOfBumpsMNC4` | 整数计数。 |
| `bC4` | `bumps.diameter` | 凸点直径 | `flipChipBumps.bumpDiameterBC4` | mm；数值。 |
| `tC4` | `bumps.height` | 凸点层厚度 | `flipChipBumps.bumpHeightTC4` | mm；数值。 |
| `MD` | `bga.columns` | X 方向焊球数 MD | `solderBalls.numberOfSolderBallsInXMD` | 整数计数。 |
| `ME` | `bga.rows` | Y 方向焊球数 ME | `solderBalls.numberOfSolderBallsInYME` | 整数计数。 |
| `e` | `bga.pitch` | 焊球间距 e | `solderBalls.ballPitchE` | mm；数值。 |
| `b` | `bga.diameter` | 焊球直径 b | `solderBalls.ballDiameterB` | mm；数值。 |
| `A1` | `bga.height` | 基板离板高度 A1 | `solderBalls.substrateStandoffA1` | mm；数值。 |
| `radio_EnCaPl` | `cover.type` | 顶部结构 | `wizard.topCover` | 空串→bare_die；c→lid；p→plate；e→encapsulant。 |
| `Le` | `cover.length` | 塑封长度 | `topCover.encapsulant.lengthLe` | mm；数值。 |
| `We` | `cover.width` | 塑封宽度 | `topCover.encapsulant.widthWe` | mm；数值。 |
| `te` | `cover.thickness` | 塑封厚度 | `topCover.encapsulant.thicknessTe` | mm；数值。 |
| `Lc` | `lid.length` | 顶盖长度 | `topCover.lid.lidLengthLc` | mm；数值。 |
| `Wc` | `lid.width` | 顶盖宽度 | `topCover.lid.lidWidthWc` | mm；数值。 |
| `tc` | `lid.thickness` | 顶盖厚度 | `topCover.lid.lidThicknessTc` | mm；数值。 |
| `tcb` | `lid.base_thickness` | 顶盖侧壁宽度 | `topCover.lid.lidBaseThicknessTcb` | mm；侧壁宽度，用于计算内腔长宽，勿按 Z 向厚度解释。 |
| `tda` | `lid.die_attach` | 顶盖芯片连接层厚度 | `topCover.lid.dieAttachThicknessTda` | mm；与 plate.die_attach 共用 tda，按顶盖分支解释。 |
| `tcadh` | `lid.adhesive` | 顶盖侧壁粘接厚度 | `topCover.lid.lidAdhesiveThickness` | mm；数值。 |
| `Lc` | `plate.length` | 热板长度 | `topCover.plate.plateLengthLc` | mm；数值。 |
| `Wc` | `plate.width` | 热板宽度 | `topCover.plate.plateWidthWc` | mm；数值。 |
| `tc` | `plate.thickness` | 热板厚度 | `topCover.plate.plateThicknessTc` | mm；数值。 |
| `tda` | `plate.die_attach` | 热板芯片连接层厚度 | `topCover.plate.dieAttachThicknessTda` | mm；与 lid.die_attach 共用 tda，按顶盖分支解释。 |
| `localgrid` | `grid.enabled` | 局部网格 | `modelingOptions.localizeGrid` | CHECKED→true；UNCHECKED→false。 |
| `radio_lgc` | `grid.density` | 网格密度 | `modelingOptions.gridDensity` | 1→coarse；2→medium；3→fine。 |
| `radio_bump_type` | `bumps.array_type` | 凸点阵列类型 | `flipChipBumps.arrayType` | 1→regular；2→non_regular。规则阵列数量为 columns×rows。 |
| `MDC4` | `bumps.columns` | X 向凸点数 MDC4 | `flipChipBumps.numberOfBumpsInXMDC4` | 按原生属性值适配。 |
| `MEC4` | `bumps.rows` | Y 向凸点数 MEC4 | `flipChipBumps.numberOfBumpsInYMEC4` | 按原生属性值适配。 |
| `c4_underfill` | `bumps.underfill` | 包含底填充 | `flipChipBumps.underfill` | CHECKED→true；UNCHECKED→false。 |
| `check_thickness` | `cover.flush` | 芯片顶面齐平 | `topCover.encapsulant.enableDieFlush` | CHECKED→true；开启后塑封厚度由芯片顶面确定。 |
| `radio_stiffener` | `stiffener.enabled` | 加强环 | `topCover.lid.stiffener` | 1→true；2→false；原生属性已确认；无 PackStudio 预设参数绑定。 |
| `Ls` | `stiffener.length` | 外框长度 Ls | `topCover.lid.stiffenerLengthLs` | mm；数值。 |
| `Ws` | `stiffener.width` | 外框宽度 Ws | `topCover.lid.stiffenerWidthWs` | mm；数值。 |
| `Lsc` | `stiffener.cavity_length` | 内腔长度 Lsc | `topCover.lid.stiffenerCavityLengthLsc` | mm；数值。 |
| `Wsc` | `stiffener.cavity_width` | 内腔宽度 Wsc | `topCover.lid.stiffenerCavityWidthWsc` | mm；数值。 |
| `tsadh` | `stiffener.adhesive` | 加强环粘接厚度 | `topCover.lid.stiffenerAdhesiveThickness` | mm；数值。 |
| `slug` | `slug.enabled` | 包含嵌入式散热块 | `dropInSlug.includeSlug` | CHECKED→true；UNCHECKED→false；原生属性已确认；FC 模板无预设参数绑定。 |
| `L_sl` | `slug.length` | 散热块长度 Lsl | `dropInSlug.slugLengthLsl` | mm；数值。 |
| `W_sl` | `slug.width` | 散热块宽度 Wsl | `dropInSlug.slugWidthWsl` | mm；数值。 |
| `t_sl` | `slug.thickness` | 散热块厚度 tsl | `dropInSlug.slugThicknessTsl` | mm；数值。 |
| `dsl` | `slug.diameter` | 散热块直径 ds | `dropInSlug.slugDiameterDs` | mm；数值。 |
| `L_slf` | `slug.foot_length` | 支脚延伸长度 Lsf | `dropInSlug.slugFootExtendLengthLsf` | mm；数值。 |
| `W_slf` | `slug.foot_width` | 支脚延伸宽度 Wsf | `dropInSlug.slugFootExtendWidthWsf` | mm；数值。 |
| `gsl` | `slug.offset` | 散热块偏移 Gs | `dropInSlug.slugOffsetGs` | mm；数值。 |
| `g_slf` | `slug.clearance` | 支脚净空 gsf | `dropInSlug.slugFootClearanceGsf` | mm；数值。 |
| `slug_adh` | `slug.adhesive_enabled` | 支脚下包含粘接层 | `dropInSlug.adhesivePresentUnderSlugFoot` | CHECKED→true；UNCHECKED→false；原生属性已确认；FC 模板无预设参数绑定。 |

### pbga_fc

| DES 原始键 | PackStudio 内部键 | 含义 | 原生属性 / 数据来源 | 单位 / 转换 / 限制 |
| --- | --- | --- | --- | --- |
| `—` | `footprint.size` | Footprint 尺寸（JEDEC） | `wizard.jedecFootprint` | 原生向导属性已确认；按家族/子类型选择。无独立 DES 键，内部保存为预设 ID。 |
| `D` | `substrate.length` | 基板长度 D | `packageSubstrate.substrateLengthD` | mm；数值。 |
| `E` | `substrate.width` | 基板宽度 E | `packageSubstrate.substrateWidthE` | mm；数值。 |
| `A2` | `substrate.thickness` | 基板厚度 A2 | `packageSubstrate.substrateThicknessA2` | mm；数值。 |
| `Ld` | `die.length` | 芯片长度 | `die.dieLengthLd` | mm；数值。 |
| `Wd` | `die.width` | 芯片宽度 | `die.dieWidthWd` | mm；数值。 |
| `td` | `die.thickness` | 芯片厚度 | `die.dieThicknessTd` | mm；数值。 |
| `P` | `die.power` | 芯片功率 | `die.packagePower` | W；数值。 |
| `MNC4` | `bumps.total` | 凸点总数 | `flipChipBumps.totalNumberOfBumpsMNC4` | 整数计数。 |
| `bC4` | `bumps.diameter` | 凸点直径 | `flipChipBumps.bumpDiameterBC4` | mm；数值。 |
| `tC4` | `bumps.height` | 凸点层厚度 | `flipChipBumps.bumpHeightTC4` | mm；数值。 |
| `MD` | `bga.columns` | X 方向焊球数 MD | `solderBalls.numberOfSolderBallsInXMD` | 整数计数。 |
| `ME` | `bga.rows` | Y 方向焊球数 ME | `solderBalls.numberOfSolderBallsInYME` | 整数计数。 |
| `e` | `bga.pitch` | 焊球间距 e | `solderBalls.ballPitchE` | mm；数值。 |
| `b` | `bga.diameter` | 焊球直径 b | `solderBalls.ballDiameterB` | mm；数值。 |
| `A1` | `bga.height` | 基板离板高度 A1 | `solderBalls.substrateStandoffA1` | mm；数值。 |
| `radio_EnCaPl` | `cover.type` | 顶部结构 | `wizard.topCover` | 空串→bare_die；c→lid；p→plate；e→encapsulant。 |
| `Le` | `cover.length` | 塑封长度 | `topCover.encapsulant.lengthLe` | mm；数值。 |
| `We` | `cover.width` | 塑封宽度 | `topCover.encapsulant.widthWe` | mm；数值。 |
| `te` | `cover.thickness` | 塑封厚度 | `topCover.encapsulant.thicknessTe` | mm；数值。 |
| `Lc` | `lid.length` | 顶盖长度 | `topCover.lid.lidLengthLc` | mm；数值。 |
| `Wc` | `lid.width` | 顶盖宽度 | `topCover.lid.lidWidthWc` | mm；数值。 |
| `tc` | `lid.thickness` | 顶盖厚度 | `topCover.lid.lidThicknessTc` | mm；数值。 |
| `tcb` | `lid.base_thickness` | 顶盖侧壁宽度 | `topCover.lid.lidBaseThicknessTcb` | mm；侧壁宽度，用于计算内腔长宽，勿按 Z 向厚度解释。 |
| `tda` | `lid.die_attach` | 顶盖芯片连接层厚度 | `topCover.lid.dieAttachThicknessTda` | mm；与 plate.die_attach 共用 tda，按顶盖分支解释。 |
| `tcadh` | `lid.adhesive` | 顶盖侧壁粘接厚度 | `topCover.lid.lidAdhesiveThickness` | mm；数值。 |
| `Lc` | `plate.length` | 热板长度 | `topCover.plate.plateLengthLc` | mm；数值。 |
| `Wc` | `plate.width` | 热板宽度 | `topCover.plate.plateWidthWc` | mm；数值。 |
| `tc` | `plate.thickness` | 热板厚度 | `topCover.plate.plateThicknessTc` | mm；数值。 |
| `tda` | `plate.die_attach` | 热板芯片连接层厚度 | `topCover.plate.dieAttachThicknessTda` | mm；与 lid.die_attach 共用 tda，按顶盖分支解释。 |
| `localgrid` | `grid.enabled` | 局部网格 | `modelingOptions.localizeGrid` | CHECKED→true；UNCHECKED→false。 |
| `radio_lgc` | `grid.density` | 网格密度 | `modelingOptions.gridDensity` | 1→coarse；2→medium；3→fine。 |
| `radio_bump_type` | `bumps.array_type` | 凸点阵列类型 | `flipChipBumps.arrayType` | 1→regular；2→non_regular。规则阵列数量为 columns×rows。 |
| `MDC4` | `bumps.columns` | X 向凸点数 MDC4 | `flipChipBumps.numberOfBumpsInXMDC4` | 按原生属性值适配。 |
| `MEC4` | `bumps.rows` | Y 向凸点数 MEC4 | `flipChipBumps.numberOfBumpsInYMEC4` | 按原生属性值适配。 |
| `c4_underfill` | `bumps.underfill` | 包含底填充 | `flipChipBumps.underfill` | CHECKED→true；UNCHECKED→false。 |
| `check_thickness` | `cover.flush` | 芯片顶面齐平 | `topCover.encapsulant.enableDieFlush` | CHECKED→true；开启后塑封厚度由芯片顶面确定。 |
| `radio_stiffener` | `stiffener.enabled` | 加强环 | `topCover.lid.stiffener` | 1→true；2→false；原生属性已确认；无 PackStudio 预设参数绑定。 |
| `Ls` | `stiffener.length` | 外框长度 Ls | `topCover.lid.stiffenerLengthLs` | mm；数值。 |
| `Ws` | `stiffener.width` | 外框宽度 Ws | `topCover.lid.stiffenerWidthWs` | mm；数值。 |
| `Lsc` | `stiffener.cavity_length` | 内腔长度 Lsc | `topCover.lid.stiffenerCavityLengthLsc` | mm；数值。 |
| `Wsc` | `stiffener.cavity_width` | 内腔宽度 Wsc | `topCover.lid.stiffenerCavityWidthWsc` | mm；数值。 |
| `tsadh` | `stiffener.adhesive` | 加强环粘接厚度 | `topCover.lid.stiffenerAdhesiveThickness` | mm；数值。 |
| `slug` | `slug.enabled` | 包含嵌入式散热块 | `dropInSlug.includeSlug` | CHECKED→true；UNCHECKED→false；原生属性已确认；FC 模板无预设参数绑定。 |
| `L_sl` | `slug.length` | 散热块长度 Lsl | `dropInSlug.slugLengthLsl` | mm；数值。 |
| `W_sl` | `slug.width` | 散热块宽度 Wsl | `dropInSlug.slugWidthWsl` | mm；数值。 |
| `t_sl` | `slug.thickness` | 散热块厚度 tsl | `dropInSlug.slugThicknessTsl` | mm；数值。 |
| `dsl` | `slug.diameter` | 散热块直径 ds | `dropInSlug.slugDiameterDs` | mm；数值。 |
| `L_slf` | `slug.foot_length` | 支脚延伸长度 Lsf | `dropInSlug.slugFootExtendLengthLsf` | mm；数值。 |
| `W_slf` | `slug.foot_width` | 支脚延伸宽度 Wsf | `dropInSlug.slugFootExtendWidthWsf` | mm；数值。 |
| `gsl` | `slug.offset` | 散热块偏移 Gs | `dropInSlug.slugOffsetGs` | mm；数值。 |
| `g_slf` | `slug.clearance` | 支脚净空 gsf | `dropInSlug.slugFootClearanceGsf` | mm；数值。 |
| `slug_adh` | `slug.adhesive_enabled` | 支脚下包含粘接层 | `dropInSlug.adhesivePresentUnderSlugFoot` | CHECKED→true；UNCHECKED→false；原生属性已确认；FC 模板无预设参数绑定。 |
| `—` | `vias.enabled` | 芯层通孔 | —（内部独立开关） | 原生 coreVias 由 groupValid() 与行列数量控制建模；isEnabled() 恒为 true。不存在已发现的一对一可编辑布尔属性，见启用机制专表。 |
| `NVx` | `vias.columns` | X 向孔数 NVx | `coreVias.numberOfThermalViasInXNVx` | 按原生属性值适配。 |
| `NVy` | `vias.rows` | Y 向孔数 NVy | `coreVias.numberOfThermalViasInYNVy` | 按原生属性值适配。 |
| `ev` | `vias.pitch` | 孔间距 ev | `coreVias.viaPitchEv` | mm；数值。 |
| `dv` | `vias.diameter` | 孔外径 dv | `coreVias.viaDiameterDv` | mm；数值。 |
| `tpl` | `vias.plating` | 镀层厚度 tpl | `coreVias.platingThicknessTpl` | mm；数值。 |
| `radio_Via_modeling` | `vias.modeling` | 芯层通孔建模 | `modelingOptions.modelCoreViasAs` | 原生 discreteCuboids→内部 discrete（DES=3）；orthotropicCuboid→equivalent（DES=4）；原生属性已确认，无预设参数绑定。 |
| `z1,z2,… / tz1,tz2,… / coverage1,coverage2,…` | `metal.layers` | 芯层金属层表（Depth / Thickness / Coverage） | `metalLayers.metalLayersTable` | 原生表格属性；row=0/1 分别保存为后缀 1/2，依次对应 depth/thickness/coverage；已验证两行，见金属层表。 |
| `—` | `upper.enabled` | 启用增层区域 | —（内部独立开关） | 原生 upperBuiltUpRegion 由 groupValid() 控制区域建模；isEnabled() 恒为 true。微通孔数量为 0 仍保留区域，见启用机制专表。 |
| `A2b1` | `upper.thickness` | 区域厚度 | `upperBuiltUpRegion.thicknessA2b1` | mm；数值。 |
| `Nb1` | `upper.count` | 微通孔总数 | `upperBuiltUpRegion.totalNumberOfMicroViasNb1` | 按原生属性值适配。 |
| `dv_b1` | `upper.diameter` | 微通孔外径 | `upperBuiltUpRegion.viaDiameterDvb1` | mm；数值。 |
| `tpl_b1` | `upper.plating` | 微通孔镀层厚度 | `upperBuiltUpRegion.platingThicknessTpl` | mm；数值。 |
| `radio_up_filled_vias` | `upper.filled` | 填充微通孔 | `upperBuiltUpRegion.filledVias` | 1→true；2→false。 |
| `zb1_i / tzb1_i / coverb1_i（i 为层槽位，样本为 1、2）` | `upper.layers` | 金属层表（全基板 Depth） | `upperBuiltUpRegion.metalLayersTable` | JSON 字符串；depth 相对全基板顶面，非增层区域自己的顶面；见专表。 |
| `—` | `lower.enabled` | 启用增层区域 | —（内部独立开关） | 原生 lowerBuiltUpRegion 由 groupValid() 控制区域建模；isEnabled() 恒为 true。微通孔数量为 0 仍保留区域，见启用机制专表。 |
| `A2b2` | `lower.thickness` | 区域厚度 | `lowerBuiltUpRegion.thicknessA2b2` | mm；数值。 |
| `Nb2` | `lower.count` | 微通孔总数 | `lowerBuiltUpRegion.totalNumberOfMicroViasNb2` | 按原生属性值适配。 |
| `dv_b2` | `lower.diameter` | 微通孔外径 | `lowerBuiltUpRegion.viaDiameterDvb2` | mm；数值。 |
| `tpl_b2` | `lower.plating` | 微通孔镀层厚度 | `lowerBuiltUpRegion.platingThicknessTpl` | mm；数值。 |
| `radio_low_filled_vias` | `lower.filled` | 填充微通孔 | `lowerBuiltUpRegion.filledVias` | 1→true；2→false。 |
| `zb2_i / tzb2_i / coverb2_i（i 为层槽位，样本为 1、2）` | `lower.layers` | 金属层表（全基板 Depth） | `lowerBuiltUpRegion.metalLayersTable` | JSON 字符串；depth 相对全基板顶面，非增层区域自己的顶面；见专表。 |

### pbga_wb

| DES 原始键 | PackStudio 内部键 | 含义 | 原生属性 / 数据来源 | 单位 / 转换 / 限制 |
| --- | --- | --- | --- | --- |
| `—` | `footprint.size` | Footprint 尺寸（JEDEC） | `wizard.jedecFootprint` | 原生向导属性已确认；按家族/子类型选择。无独立 DES 键，内部保存为预设 ID。 |
| `D` | `package.length` | 基板长度 D | `packageSubstrate.substrateLengthD` | mm；数值。 |
| `E` | `package.width` | 基板宽度 E | `packageSubstrate.substrateWidthE` | mm；数值。 |
| `A2` | `substrate.thickness` | 基板厚度 A2 | `packageSubstrate.substrateThicknessA2` | mm；数值。 |
| `tz1` | `trace.top_thickness` | 顶部金属层厚度 | `wizard.topSignalLayerThickness` | mm；数值。 |
| `tz6` | `trace.bottom_thickness` | 底部金属层厚度 | `wizard.bottomSignalLayerThickness` | mm；数值。 |
| `Le` | `encapsulant.length` | 塑封长度 | `encapsulant.lengthLe` | mm；数值。 |
| `We` | `encapsulant.width` | 塑封宽度 | `encapsulant.widthWe` | mm；数值。 |
| `te` | `encapsulant.thickness` | 塑封厚度 | `encapsulant.thicknessTe` | mm；数值。 |
| `Lf` | `flag.length` | 芯片承载台长度 Lf | `dieFlagAndSolderMask.dieFlagLf` | mm；数值。 |
| `Wf` | `flag.width` | 芯片承载台宽度 Wf | `dieFlagAndSolderMask.dieFlagWf` | mm；数值。 |
| `tsm` | `solder_mask.thickness` | 阻焊层厚度 | `dieFlagAndSolderMask.solderMaskThickness` | mm；数值。 |
| `Ld` | `die.length` | 芯片长度 | `die.dieLengthLd` | mm；数值。 |
| `Wd` | `die.width` | 芯片宽度 | `die.dieWidthWd` | mm；数值。 |
| `td` | `die.thickness` | 芯片厚度 | `die.dieThicknessTd` | mm；数值。 |
| `tda` | `die.attach` | 粘接层厚度 | `die.dieAttachThicknessTda` | mm；数值。 |
| `P` | `die.power` | 芯片功率 | `die.packagePower` | W；数值。 |
| `Nw` | `bond_wire.total` | 键合线总数 | `die.numberOfBondWiresNw` | 整数计数。 |
| `Lw` | `bond_wire.extent_length` | 键合焊盘长度范围 | `die.bondWireExtentLengthLw` | mm；数值。 |
| `Ww` | `bond_wire.extent_width` | 键合焊盘宽度范围 | `die.bondWireExtentWidthWw` | mm；数值。 |
| `dw` | `bond_wire.diameter` | 键合线等效宽度 | `die.bondWireDiameterDw` | mm；数值。 |
| `—` | `vias.enabled` | 包含热通孔 | `thermalVias（数据组状态）` | 预设绑定读取原生组 enabled 状态；该状态不是可由 modify_component 修改的同名布尔属性。内部开关独立控制是否创建通孔。 |
| `NVx` | `vias.columns` | 通孔 X 方向数量 | `thermalVias.numberOfThermalViasInXNVx` | 整数计数。 |
| `NVy` | `vias.rows` | 通孔 Y 方向数量 | `thermalVias.numberOfThermalViasInYNVy` | 整数计数。 |
| `ev` | `vias.pitch` | 通孔间距 | `thermalVias.viaPitchEv` | mm；数值。 |
| `dv` | `vias.diameter` | 通孔直径 | `thermalVias.viaDiameterDv` | mm；数值。 |
| `tpl` | `vias.plating` | 通孔镀层厚度 | `thermalVias.platingThicknessTpl` | mm；数值。 |
| `MD` | `bga.columns` | X 方向焊球数 MD | `solderBalls.numberOfSolderBallsInXMD` | 整数计数。 |
| `ME` | `bga.rows` | Y 方向焊球数 ME | `solderBalls.numberOfSolderBallsInYME` | 整数计数。 |
| `e` | `bga.pitch` | 焊球间距 e | `solderBalls.ballPitchE` | mm；数值。 |
| `b` | `bga.diameter` | 焊球直径 b | `solderBalls.ballDiameterB` | mm；数值。 |
| `A1` | `bga.height` | 基板离板高度 A1 | `solderBalls.substrateStandoffA1` | mm；数值。 |
| `backside_spreader` | `spreader.enabled` | 启用背面扩散片 | `backsideSpreader.includeBacksideSpreader` | CHECKED→true；UNCHECKED→false。 |
| `L_spr` | `spreader.length` | 扩散片长度 Lspr | `backsideSpreader.spreaderLengthLspr` | mm；数值。 |
| `W_spr` | `spreader.width` | 扩散片宽度 Wspr | `backsideSpreader.spreaderWidthWspr` | mm；数值。 |
| `t_spr` | `spreader.thickness` | 扩散片厚度 tspr | `backsideSpreader.spreaderThicknessTspr` | mm；数值。 |
| `Lbt` | `spreader.hole_length` | 底层走线开口长度 Lbt | `backsideSpreader.bottomTraceHoleLengthLbt` | mm；数值。 |
| `Wbt` | `spreader.hole_width` | 底层走线开口宽度 Wbt | `backsideSpreader.bottomTraceHoleWidthWbt` | mm；数值。 |
| `localgrid` | `grid.enabled` | 局部网格 | `modelingOptions.localizeGrid` | CHECKED→true；UNCHECKED→false。 |
| `radio_lgc` | `grid.density` | 网格密度 | `modelingOptions.gridDensity` | 1→coarse；2→medium；3→fine。 |
| `radio_Bond_Wires_modeling` | `bond_wire.modeling` | 键合线建模方式 | `modelingOptions.modelBondWiresAs` | 2→isotropicCuboid；4→orthotropicCuboid。 |
| `—` | `substrate.layers` | 基板层数 | `wizard.substrateLayer` | 原生向导 substrateLayer；无独立 DES 键，不能只凭已填充的表格槽位推定。 |
| `cf` | `flag.coverage` | 承载台金属覆盖率 Cf | `dieFlagAndSolderMask.coveragePercentageCf` | %；数值。 |
| `tz1,tz2,tz3,tz6 / z2,z3 / coverage1,coverage2,coverage3,coverage6 / via_con1…via_con6` | `metal.layers` | 金属层表 | `metalLayers.metalLayersTable` | 原生表格属性；运行预设的 metal_layers 为展开后的派生行数据，非原生属性名。 |
| `radio_Via_modeling` | `vias.modeling` | 通孔建模方式 | `modelingOptions.modelThermalViasAs` | 2→isotropicCuboid；3→discreteCuboids；4→orthotropicCuboid。 |
| `slug` | `slug.enabled` | 包含嵌入式散热块 | `dropInSlug.includeSlug` | CHECKED→true；UNCHECKED→false。 |
| `L_sl` | `slug.length` | 散热块长度 Lsl | `dropInSlug.slugLengthLsl` | mm；数值。 |
| `W_sl` | `slug.width` | 散热块宽度 Wsl | `dropInSlug.slugWidthWsl` | mm；数值。 |
| `t_sl` | `slug.thickness` | 散热块厚度 tsl | `dropInSlug.slugThicknessTsl` | mm；数值。 |
| `dsl` | `slug.diameter` | 散热块直径 ds | `dropInSlug.slugDiameterDs` | mm；数值。 |
| `L_slf` | `slug.foot_length` | 支脚延伸长度 Lsf | `dropInSlug.slugFootExtendLengthLsf` | mm；数值。 |
| `W_slf` | `slug.foot_width` | 支脚延伸宽度 Wsf | `dropInSlug.slugFootExtendWidthWsf` | mm；数值。 |
| `gsl` | `slug.offset` | 散热块偏移 Gs | `dropInSlug.slugOffsetGs` | mm；数值。 |
| `g_slf` | `slug.clearance` | 支脚净空 gsf | `dropInSlug.slugFootClearanceGsf` | mm；数值。 |
| `slug_adh` | `slug.adhesive_enabled` | 支脚下包含粘接层 | `dropInSlug.adhesivePresentUnderSlugFoot` | CHECKED→true；UNCHECKED→false。 |

### chip_array

| DES 原始键 | PackStudio 内部键 | 含义 | 原生属性 / 数据来源 | 单位 / 转换 / 限制 |
| --- | --- | --- | --- | --- |
| `—` | `footprint.size` | Footprint 尺寸（JEDEC） | `wizard.jedecFootprint` | 原生向导属性已确认；按家族/子类型选择。无独立 DES 键，内部保存为预设 ID。 |
| `D` | `package.length` | 封装长度 D | `overallPackage.lengthD` | mm；数值。 |
| `E` | `package.width` | 封装宽度 E | `overallPackage.widthE` | mm；数值。 |
| `A2` | `substrate.thickness` | 基板厚度 A2 | `overallPackage.substrateThicknessA2` | mm；数值。 |
| `tza1（2 层）/ tz1（4 层）` | `trace.top_thickness` | 顶部金属层厚度 | `wizard.topSignalLayerThickness` | mm；数值。 |
| `tza2（2 层）/ tz4（4 层）` | `trace.bottom_thickness` | 底部金属层厚度 | `wizard.bottomSignalLayerThickness` | mm；数值。 |
| `Ld` | `die.length` | 芯片长度 | `die.dieLengthLd` | mm；数值。 |
| `Wd` | `die.width` | 芯片宽度 | `die.dieWidthWd` | mm；数值。 |
| `td` | `die.thickness` | 芯片厚度 | `die.dieThicknessTd` | mm；数值。 |
| `tda` | `die.attach` | 粘接层厚度 | `die.dieAttachThicknessTda` | mm；数值。 |
| `P` | `die.power` | 芯片功率 | `die.packagePower` | W；数值。 |
| `te` | `encapsulant.thickness` | 塑封厚度 | `encapsulant.thicknessTe` | mm；数值。 |
| `tsm` | `solder_mask.thickness` | 阻焊层厚度 | `encapsulant.solderMaskThicknessTsm` | mm；数值。 |
| `Lw` | `bond_wire.extent_length` | 键合焊盘长度范围 | `bondWires.extentOfBondWirePadsLw` | mm；数值。 |
| `Ww` | `bond_wire.extent_width` | 键合焊盘宽度范围 | `bondWires.extentOfBondWirePadsWw` | mm；数值。 |
| `dw` | `bond_wire.diameter` | 键合线等效宽度 | `bondWires.bondWireDiameterDw` | mm；数值。 |
| `—` | `vias.enabled` | 包含热通孔 | `vias（数据组状态）` | 预设绑定读取原生组 enabled 状态；该状态不是可由 modify_component 修改的同名布尔属性。内部开关独立控制是否创建通孔。 |
| `dv` | `vias.diameter` | 通孔直径 | `vias.viaDiameterDv` | mm；数值。 |
| `tpl` | `vias.plating` | 通孔镀层厚度 | `vias.platingThicknessTpl` | mm；数值。 |
| `vxoff` | `vias.offset_x` | 通孔 X 偏移 | `modelingOptions.viaOffsetInX` | mm；数值。 |
| `vyoff` | `vias.offset_y` | 通孔 Y 偏移 | `modelingOptions.viaOffsetInY` | mm；数值。 |
| `MD` | `bga.columns` | X 方向焊球数 MD | `solderBalls.numberOfSolderBallsInXMD` | 整数计数。 |
| `ME` | `bga.rows` | Y 方向焊球数 ME | `solderBalls.numberOfSolderBallsInYME` | 整数计数。 |
| `e` | `bga.pitch` | 焊球间距 e | `solderBalls.ballPitchE` | mm；数值。 |
| `b` | `bga.diameter` | 焊球直径 b | `solderBalls.ballDiameterB` | mm；数值。 |
| `A1` | `bga.height` | 基板离板高度 A1 | `solderBalls.substrateStandoffA1` | mm；数值。 |
| `localgrid` | `grid.enabled` | 局部网格 | `modelingOptions.localizeGrid` | CHECKED→true；UNCHECKED→false。 |
| `radio_lgc` | `grid.density` | 网格密度 | `modelingOptions.gridDensity` | 1→coarse；2→medium；3→fine。 |
| `num_metal_layers` | `substrate.layers` | 基板层数 | `metalLayers.substrateLayer / wizard.substrateLayer` | 1→2-Layer；2→4-Layer；组件与向导属性均确认存在，组件改值与向导初始化的联动范围不同。 |
| `radio_default_bwNumber` | `bond_wire.auto_count` | 键合线数量等于焊球 | `bondWires.numberBondWiresEqualsSolderBalls` | 1→true；2→false；true 时键合线数量按焊球数量计算。 |
| `Nw` | `bond_wire.total` | 键合线总数 Nw | `bondWires.numberOfBondWiresNw` | 按原生属性值适配。 |
| `radio_BW_modeling` | `bond_wire.include` | 包含键合线 | `modelingOptions.bondWireModeling` | 原生 include→true（DES=1）；ignore→false（DES=2）；原生属性已确认，无预设参数绑定。 |
| `radio_filled_vias` | `vias.filled` | 填充通孔 | `vias.filledVias` | 1→true；2→false。 |
| `radio_Via_modeling` | `vias.modeling` | 通孔建模 | `modelingOptions.viaModeling` | 3→approximate；5→accurate。 |
| `tza1,tza2 / coveragea1,coveragea2（2 层）；tz1…tz4 / z2,z3 / coverage1…coverage4（4 层）` | `metal.layers` | 金属层表（Depth / Thickness / Coverage） | `metalLayers.twoLayerMetalLayersTable / metalLayers.fourLayerMetalLayersTable` | 原生表格属性；运行预设的 metal_layers 为展开后的派生行数据，非原生属性名。 |
| `Lml` | `metal.hole_length` | 顶层中央区域长度 Lml | `metalLayers.lengthLml` | mm；数值。 |
| `Wml` | `metal.hole_width` | 顶层中央区域宽度 Wml | `metalLayers.widthWml` | mm；数值。 |

### qfn

| DES 原始键 | PackStudio 内部键 | 含义 | 原生属性 / 数据来源 | 单位 / 转换 / 限制 |
| --- | --- | --- | --- | --- |
| `—` | `footprint.size` | Footprint 尺寸（JEDEC） | `wizard.jedecFootprint` | 原生向导属性已确认；按家族/子类型选择。无独立 DES 键，内部保存为预设 ID。 |
| `D` | `package.length` | 封装长度 D | `overallPackage.lengthD` | mm；数值。 |
| `E` | `package.width` | 封装宽度 E | `overallPackage.widthE` | mm；数值。 |
| `A1` | `package.standoff` | 离板高度 A1 | `overallPackage.standoffA1` | mm；数值。 |
| `A2` | `encapsulant.thickness` | 塑封厚度 A2 | `overallPackage.encapsulantThicknessA2` | mm；数值。 |
| `Ld` | `die.length` | 芯片长度 | `die.dieLengthLd` | mm；数值。 |
| `Wd` | `die.width` | 芯片宽度 | `die.dieWidthWd` | mm；数值。 |
| `td` | `die.thickness` | 芯片厚度 | `die.dieThicknessTd` | mm；数值。 |
| `tda` | `die.attach` | 粘接层厚度 | `die.dieAttachThicknessTda` | mm；数值。 |
| `P` | `die.power` | 芯片功率 | `die.packagePower` | W；数值。 |
| `Lp` | `pad.length` | DAP 长度 Lp | `dap.dapLengthLp` | mm；数值。 |
| `Wp` | `pad.width` | DAP 宽度 Wp | `dap.dapWidthWp` | mm；数值。 |
| `Lep` | `pad.exposed_length` | 底部裸露长度 | `dap.exposedPADLength` | mm；数值。 |
| `Wep` | `pad.exposed_width` | 底部裸露宽度 | `dap.exposedPADWidth` | mm；数值。 |
| `MD` | `leads.count_x` | 上下侧引脚数 MD | `leadAndSolderInterconnect.numberOfLeadsOnTopBottomMD` | 整数计数。 |
| `ME` | `leads.count_y` | 左右侧引脚数 ME | `leadAndSolderInterconnect.numberOfLeadsOnLeftRightME` | 整数计数。 |
| `ex` | `leads.pitch_x` | X 向引脚间距 ex | `leadAndSolderInterconnect.pitchInXDirectionEx` | mm；数值。 |
| `ey` | `leads.pitch_y` | Y 向引脚间距 ey | `leadAndSolderInterconnect.pitchInYDirectionEy` | mm；数值。 |
| `wf` | `leads.width` | 引脚宽度 b | `leadAndSolderInterconnect.leadWidthB` | mm；数值。 |
| `lf` | `leads.length` | 外露引脚长度 L | `leadAndSolderInterconnect.exposedLeadLengthL` | mm；数值。 |
| `hf` | `leads.exposed_thickness` | 外露引脚厚度 | `leadAndSolderInterconnect.exposedLeadThickness` | mm；数值。 |
| `tf` | `leads.thickness` | 引脚总厚度 A3 | `leadAndSolderInterconnect.leadThicknessA3` | mm；数值。 |
| `ldent` | `leads.etch` | 引脚蚀刻量 | `leadAndSolderInterconnect.leadEtch` | mm；数值。 |
| `lbwx` | `bond_wire.length_x` | 左右键合线长度 | `bondWires.bondWireLengthOnLeftRightLbwx` | mm；数值。 |
| `lbwy` | `bond_wire.length_y` | 上下键合线长度 | `bondWires.bondWireLengthOnTopBottomLbwy` | mm；数值。 |
| `dbw` | `bond_wire.diameter` | 键合线等效宽度 | `bondWires.bondWireDiameterDbw` | mm；数值。 |
| `isLand` | `thermal_land.enabled` | 包含散热焊盘 | `thermalLand.includeLand` | CHECKED→true；UNCHECKED→false。 |
| `ts` | `thermal_land.thickness` | 散热焊盘厚度 | `thermalLand.landThickness` | mm；thermalLand.landThickness=0.08 回放保存为 ts=0.08。 |
| `radio_via_modeling` | `vias.enabled` | 启用热通孔 | `vias.modelViasAs` | 1/2→true；3（ignored）→false。 |
| `lv` | `vias.length` | 通孔长度 Lv | `vias.viasLengthLv` | mm；数值。 |
| `dv` | `vias.diameter` | 通孔直径 Dv | `vias.viasDiameterDv` | mm；数值。 |
| `tpl` | `vias.plating` | 通孔镀层厚度 tpl | `vias.platingThicknessTpl` | mm；数值。 |
| `ev` | `vias.pitch` | 通孔间距 ev | `vias.viasPitchEv` | mm；数值。 |
| `VD` | `vias.columns` | 通孔 X 方向数量 VD | `vias.numberOfViasInXVD` | 整数计数。 |
| `VE` | `vias.rows` | 通孔 Y 方向数量 VE | `vias.numberOfViasInYVE` | 整数计数。 |
| `localgrid` | `grid.enabled` | 局部网格 | `modelingOptions.localizeGrid` | CHECKED→true；UNCHECKED→false。 |
| `radio_lgc` | `grid.density` | 网格密度 | `modelingOptions.gridDensity` | 1→coarse；2→medium；3→fine。 |
| `radio_LeadFram_modeling` | `leads.modeling` | 引脚与焊料互连建模方式 | `modelingOptions.modelLeadAndSolderInterconnectAs` | 1→discreteLeads；2→orthotropicCuboid。 |
| `nsteps` | `bond_wire.steps` | 键合线离散分段数量 | `modelingOptions.numberOfDiscreteBondwireSteps` | 整数；原生未指定或存储值<2时有效值为1。 |
| `radio_via_modeling` | `vias.modeling` | 通孔建模方式 | `vias.modelViasAs` | 1→discrete；2→lumped；3→关闭，预设适配将 modeling 置 discrete、enabled 置 false。 |

### pqfp

| DES 原始键 | PackStudio 内部键 | 含义 | 原生属性 / 数据来源 | 单位 / 转换 / 限制 |
| --- | --- | --- | --- | --- |
| `—` | `package.type` | Package Type | `wizard.pqfpPackageType` | 原生向导子类型；DES 的 package 仅标识家族，不能单独恢复此字段。 |
| `—` | `footprint.size` | Footprint 尺寸（JEDEC） | `wizard.lqfpJedecFootprint / wizard.mqfpJedecFootprint / wizard.tqfpJedecFootprint` | 原生向导属性已确认；按家族/子类型选择。无独立 DES 键，内部保存为预设 ID。 |
| `D` | `package.length` | 引脚外包络长度 D | `overallPackage.lengthD` | mm；数值。 |
| `E` | `package.width` | 引脚外包络宽度 E | `overallPackage.widthE` | mm；数值。 |
| `A1` | `package.standoff` | 离板高度 A1 | `overallPackage.standoffA1` | mm；数值。 |
| `D1` | `body.length` | 塑封长度 | `encapsulant.lengthD1` | mm；数值。 |
| `E1` | `body.width` | 塑封宽度 | `encapsulant.widthE1` | mm；数值。 |
| `A2` | `body.thickness` | 塑封厚度 | `encapsulant.thicknessA2` | mm；数值。 |
| `Ld` | `die.length` | 芯片长度 | `die.dieLengthLd` | mm；数值。 |
| `Wd` | `die.width` | 芯片宽度 | `die.dieWidthWd` | mm；数值。 |
| `td` | `die.thickness` | 芯片厚度 | `die.dieThicknessTd` | mm；数值。 |
| `tda` | `die.attach` | 粘接层厚度 | `die.dieAttachThicknessTda` | mm；数值。 |
| `P` | `die.power` | 芯片功率 | `die.packagePower` | W；数值。 |
| `Lf` | `flag.length` | 芯片承载台长度 Lf | `dieFlagAndTieBars.dieFlagLf` | mm；数值。 |
| `Wf` | `flag.width` | 芯片承载台宽度 Wf | `dieFlagAndTieBars.dieFlagWf` | mm；数值。 |
| `cf` | `flag.coverage` | 承载台金属覆盖率 | `dieFlagAndTieBars.metalCoverageForDieFlagCf` | %；数值。 |
| `ddf` | `flag.downset` | 承载台下沉量 | `dieFlagAndTieBars.dieFlagDownsetDdf` | mm；数值。 |
| `wtb` | `tie_bar.width` | 连接筋宽度 | `dieFlagAndTieBars.tieBarWidthWtb` | mm；数值。 |
| `MD` | `leads.count_x` | 上下侧引脚数 | `leadFrame.numberOfLeadsOnTopBottomMD` | 整数计数。 |
| `ME` | `leads.count_y` | 左右侧引脚数 | `leadFrame.numberOfLeadsOnLeftRightME` | 整数计数。 |
| `e` | `leads.pitch` | 引脚间距 | `leadFrame.pitchE` | mm；数值。 |
| `b` | `leads.width` | 引脚宽度 | `leadFrame.leadWidthB` | mm；数值。 |
| `tl` | `leads.thickness` | 引脚厚度 | `leadFrame.leadThicknessTl` | mm；数值。 |
| `hl` | `leads.height` | 引线框高度 | `leadFrame.leadframeHeightHl` | mm；数值。 |
| `wl` | `leads.foot_length` | 引脚脚长 | `leadFrame.leadfootLengthWl` | mm；数值。 |
| `g1` | `leads.gap_x` | 左右引脚间隙 | `leadFrame.leadframeFlagGapG1` | mm；数值。 |
| `g2` | `leads.gap_y` | 上下引脚间隙 | `leadFrame.leadframeFlagGapG2` | mm；数值。 |
| `lbwx` | `bond_wire.length_x` | 左右键合区域长度 | `bondWires.bondWireLengthOnLeftRightLbwx` | mm；数值。 |
| `lbwy` | `bond_wire.length_y` | 上下键合区域长度 | `bondWires.bondWireLengthOnTopBottomLbwy` | mm；数值。 |
| `N` | `bond_wire.count` | 键合线数量 | `bondWires.numberOfBondWiresN` | 整数计数。 |
| `dbw` | `bond_wire.diameter` | 键合线等效宽度 | `bondWires.bondWireDiameterDbw` | mm；数值。 |
| `landsolder` | `thermal_land.enabled` | 包含散热焊盘与焊料 | `thermalLandAndSolder.includeThermalLandAndSolder` | CHECKED→true；UNCHECKED→false。 |
| `ts` | `thermal_land.thickness` | 散热焊盘厚度 | `thermalLandAndSolder.landThickness` | mm；数值。 |
| `localgrid` | `grid.enabled` | 局部网格 | `modelingOptions.localizeGrid` | CHECKED→true；UNCHECKED→false。 |
| `radio_lgc` | `grid.density` | 网格密度 | `modelingOptions.gridDensity` | 1→coarse；2→medium；3→fine。 |
| `radio_BondWire_modeling` | `bond_wire.modeling` | 键合线建模方式 | `modelingOptions.modelBondWiresAs` | 1→isotropicCuboid；2→orthotropicCuboid。 |
| `—` | `package.exposed_pad` | 裸露焊盘初始化 | `wizard.exposedPad` | 原生向导 exposedPad；无独立 DES 键。true 初始化 flag.downset=leads.height、thermal_land.enabled=true、thermal_land.thickness=0.07 mm。 |
| `radio_defined_coverage` | `leads.custom_coverage` | 自定义引线框覆盖率 | `leadFrame.userDefinedLeadframeCoverage` | 1→true；2→false。 |
| `cl` | `leads.coverage` | 内部引线框覆盖率 | `leadFrame.leadframeCoveragePercentage` | 显式覆盖率；未指定且采用默认覆盖时为 100×b/e（%）。 |
| `radio_LeadFram_modeling` | `leads.modeling` | 引线框建模方式 | `modelingOptions.modelLeadFrameAs` | 1→isotropicCuboid；2→orthotropicCuboid。 |

### sop

| DES 原始键 | PackStudio 内部键 | 含义 | 原生属性 / 数据来源 | 单位 / 转换 / 限制 |
| --- | --- | --- | --- | --- |
| `—` | `package.type` | Package Type | `wizard.sopPackageType` | 原生向导子类型；DES 的 package 仅标识家族，不能单独恢复此字段。 |
| `—` | `footprint.size` | Footprint 尺寸（JEDEC） | `wizard.sopJedecFootprint / wizard.ssopJedecFootprint / wizard.tsopJedecFootprint / wizard.tssopJedecFootprint` | 原生向导属性已确认；按家族/子类型选择。无独立 DES 键，内部保存为预设 ID。 |
| `D` | `package.length` | 封装长度 D | `overallPackage.lengthD` | mm；数值。 |
| `E` | `package.width` | 引脚外包络宽度 E | `overallPackage.widthE` | mm；数值。 |
| `A1` | `package.standoff` | 离板高度 A1 | `overallPackage.standoffA1` | mm；数值。 |
| `D1` | `body.length` | 塑封长度 | `encapsulant.lengthD1` | mm；数值。 |
| `E1` | `body.width` | 塑封宽度 | `encapsulant.widthE1` | mm；数值。 |
| `A2` | `body.thickness` | 塑封厚度 | `encapsulant.thicknessA2` | mm；数值。 |
| `Ld` | `die.length` | 芯片长度 | `die.dieLengthLd` | mm；数值。 |
| `Wd` | `die.width` | 芯片宽度 | `die.dieWidthWd` | mm；数值。 |
| `td` | `die.thickness` | 芯片厚度 | `die.dieThicknessTd` | mm；数值。 |
| `tda` | `die.attach` | 粘接层厚度 | `die.dieAttachThicknessTda` | mm；数值。 |
| `P` | `die.power` | 芯片功率 | `die.packagePower` | W；数值。 |
| `Lf` | `flag.length` | 芯片承载台长度 Lf | `dieFlagAndTieBars.dieFlagLf` | mm；数值。 |
| `Wf` | `flag.width` | 芯片承载台宽度 Wf | `dieFlagAndTieBars.dieFlagWf` | mm；数值。 |
| `tf` | `flag.thickness` | 承载台厚度 tf | `dieFlagAndTieBars.dieFlagThicknessTf` | mm；数值。 |
| `cf` | `flag.coverage` | 承载台金属覆盖率 | `dieFlagAndTieBars.metalCoverageForDieFlagCf` | %；数值。 |
| `ddf` | `flag.downset` | 承载台下沉量 | `dieFlagAndTieBars.dieFlagDownsetDdf` | mm；数值。 |
| `wtb` | `tie_bar.width` | 连接筋宽度 | `dieFlagAndTieBars.tieBarWidthWtb` | mm；数值。 |
| `MT` | `leads.total` | 引脚总数 | `leadFrame.totalNumberOfLeadsMT` | 整数计数。 |
| `g1` | `leads.gap` | 引线框间隙 | `leadFrame.leadframeFlagGapG1` | mm；数值。 |
| `e` | `leads.pitch` | 引脚间距 | `leadFrame.pitchE` | mm；数值。 |
| `b` | `leads.width` | 引脚宽度 | `leadFrame.leadWidthB` | mm；数值。 |
| `tl` | `leads.thickness` | 引脚厚度 | `leadFrame.leadThicknessTl` | mm；数值。 |
| `hl` | `leads.height` | 引线框高度 | `leadFrame.leadframeHeightHl` | mm；数值。 |
| `Lft` | `leads.foot_length` | 引脚脚长 | `leadFrame.leadfootLengthLft` | mm；数值。 |
| `N` | `bond_wire.count` | 键合线数量 | `bondWires.numberOfBondWiresN` | 整数计数。 |
| `dbw` | `bond_wire.diameter` | 键合线等效宽度 | `bondWires.bondWireDiameterDbw` | mm；数值。 |
| `landsolder` | `thermal_land.enabled` | 包含散热焊盘与焊料 | `thermalLandAndSolder.includeThermalLandAndSolder` | CHECKED→true；UNCHECKED→false。 |
| `ts` | `thermal_land.thickness` | 散热焊盘厚度 | `thermalLandAndSolder.landThickness` | mm；数值。 |
| `localgrid` | `grid.enabled` | 局部网格 | `modelingOptions.localizeGrid` | CHECKED→true；UNCHECKED→false。 |
| `radio_lgc` | `grid.density` | 网格密度 | `modelingOptions.gridDensity` | 1→coarse；2→medium；3→fine。 |
| `radio_BondWire_modeling` | `bond_wire.modeling` | 键合线建模方式 | `modelingOptions.modelBondWiresAs` | 1→isotropicCuboid；2→orthotropicCuboid。 |
| `—` | `package.exposed_pad` | 裸露焊盘初始化 | `wizard.exposedPad` | 原生向导 exposedPad；无独立 DES 键。true 初始化 flag.downset=leads.height、thermal_land.enabled=true、thermal_land.thickness=0.07 mm。 |
| `radio_defined_coverage` | `leads.custom_coverage` | 自定义引线框覆盖率 | `leadFrame.userDefinedLeadframeCoverage` | 1→true；2→false。 |
| `cl` | `leads.coverage` | 内部引线框覆盖率 | `leadFrame.leadframeCoveragePercentage` | 显式覆盖率；未指定且采用默认覆盖时为 100×b/e（%）。 |

## 材料字段

目标均为 `ProjectDocument.Assignments["group-id"]`，CLI 对应 `material_assignments["group-id"]`。DES 值是完整材料名称，内部值是材料 ID，须经 `MaterialLibrary.IdForName` 解析；`k_*` 不是数值导热率。未指定的可选材料不应以空 ID 覆盖默认材料。

| 家族 | DES 原始键 | 内部材料组 | 含义 / 适配说明 |
| --- | --- | --- | --- |
| `bare_die` | `radio_die` | `group-die` | 芯片材料；原生 die.dieMaterial 枚举 Si/GaAs；radio_die=1→Si、2→GaAs，GaAs 已通过回放验证。 |
| `bare_die` | `k_solder` | `group-bump-solder` | 凸点焊料；名称→材料 ID；模板可选，未纳入原生预设材料绑定。 |
| `bare_die` | `k_fill` | `group-underfill` | 底部填充材料；名称→材料 ID；模板可选，未纳入原生预设材料绑定。 |
| `cbga_fc` | `k_substr` | `group-substrate` | 陶瓷基板材料；名称→材料 ID |
| `cbga_fc` | `—` | `group-die` | 芯片材料；原生固定 Silicon (Pure)，DES 无可编辑芯片材料键；内部支持独立选材。 |
| `cbga_fc` | `k_encap` | `group-encapsulant` | 塑封材料；名称→材料 ID |
| `cbga_fc` | `k_cap` | `group-lid` | 顶盖材料；名称→材料 ID |
| `cbga_fc` | `k_cadh` | `group-lid-adhesive` | 顶盖侧壁粘接材料；名称→材料 ID |
| `cbga_fc` | `kda` | `group-lid-die-attach` | 顶盖芯片连接材料；名称→材料 ID |
| `cbga_fc` | `k_cap` | `group-plate` | 热板材料；名称→材料 ID |
| `cbga_fc` | `kda` | `group-plate-die-attach` | 热板芯片连接材料；名称→材料 ID |
| `cbga_fc` | `k_C4` | `group-bump-solder` | 凸点焊料；名称→材料 ID |
| `cbga_fc` | `k_underfill` | `group-underfill` | 底部填充材料；名称→材料 ID |
| `cbga_fc` | `k_solder` | `group-bga-solder` | BGA 焊球材料；名称→材料 ID |
| `cbga_fc` | `k_stiff` | `group-stiffener` | 加强环材料；名称→材料 ID；模板可选，未纳入原生预设材料绑定。 |
| `cbga_fc` | `k_sadh` | `group-stiffener-adhesive` | 加强环粘接材料；名称→材料 ID；模板可选，未纳入原生预设材料绑定。 |
| `cbga_fc` | `k_sl` | `group-slug` | 散热块材料；名称→材料 ID；模板可选，未纳入原生预设材料绑定。 |
| `cbga_fc` | `k_slad` | `group-slug-adhesive` | 支脚粘接材料；名称→材料 ID；模板可选，未纳入原生预设材料绑定。 |
| `pbga_fc` | `k_substr` | `group-substrate` | 有机基板材料；名称→材料 ID |
| `pbga_fc` | `—` | `group-die` | 芯片材料；原生固定 Silicon (Pure)，DES 无可编辑芯片材料键；内部支持独立选材。 |
| `pbga_fc` | `k_encap` | `group-encapsulant` | 塑封材料；名称→材料 ID |
| `pbga_fc` | `k_cap` | `group-lid` | 顶盖材料；名称→材料 ID |
| `pbga_fc` | `k_cadh` | `group-lid-adhesive` | 顶盖侧壁粘接材料；名称→材料 ID |
| `pbga_fc` | `kda` | `group-lid-die-attach` | 顶盖芯片连接材料；名称→材料 ID |
| `pbga_fc` | `k_cap` | `group-plate` | 热板材料；名称→材料 ID |
| `pbga_fc` | `kda` | `group-plate-die-attach` | 热板芯片连接材料；名称→材料 ID |
| `pbga_fc` | `k_C4` | `group-bump-solder` | 凸点焊料；名称→材料 ID |
| `pbga_fc` | `k_underfill` | `group-underfill` | 底部填充材料；名称→材料 ID |
| `pbga_fc` | `k_solder` | `group-bga-solder` | BGA 焊球材料；名称→材料 ID |
| `pbga_fc` | `k_stiff` | `group-stiffener` | 加强环材料；名称→材料 ID；模板可选，未纳入原生预设材料绑定。 |
| `pbga_fc` | `k_sadh` | `group-stiffener-adhesive` | 加强环粘接材料；名称→材料 ID；模板可选，未纳入原生预设材料绑定。 |
| `pbga_fc` | `k_sl` | `group-slug` | 散热块材料；名称→材料 ID；模板可选，未纳入原生预设材料绑定。 |
| `pbga_fc` | `k_slad` | `group-slug-adhesive` | 支脚粘接材料；名称→材料 ID；模板可选，未纳入原生预设材料绑定。 |
| `pbga_fc` | `k_metal` | `group-metal` | 金属材料；名称→材料 ID |
| `pbga_fc` | `kb1` | `group-upper` | 增层介质；名称→材料 ID；模板可选，未纳入原生预设材料绑定。 |
| `pbga_fc` | `kb2` | `group-lower` | 增层介质；名称→材料 ID；模板可选，未纳入原生预设材料绑定。 |
| `pbga_wb` | `k_substr` | `group-substrate` | 基板材料；名称→材料 ID |
| `pbga_wb` | `—` | `group-die` | 芯片材料；原生固定 Silicon (Pure)，DES 无可编辑芯片材料键；内部支持独立选材。 |
| `pbga_wb` | `k_da` | `group-die-attach` | 芯片粘接材料；名称→材料 ID |
| `pbga_wb` | `k_encap` | `group-encapsulant` | 塑封材料；名称→材料 ID |
| `pbga_wb` | `k_wire` | `group-bond-wires` | 键合线材料；名称→材料 ID |
| `pbga_wb` | `ksm` | `group-solder-mask` | 阻焊层材料；名称→材料 ID |
| `pbga_wb` | `k_solder` | `group-bga-solder` | BGA 焊球材料；名称→材料 ID |
| `pbga_wb` | `k_spr` | `group-backside-spreader` | 扩散片材料；名称→材料 ID |
| `pbga_wb` | `k_metal` | `group-traces` | 金属层材料；名称→材料 ID |
| `pbga_wb` | `k_sl` | `group-slug` | 散热块材料；名称→材料 ID |
| `pbga_wb` | `k_slad` | `group-slug-adhesive` | 支脚粘接材料；名称→材料 ID |
| `chip_array` | `k_substr` | `group-substrate` | 基板材料；名称→材料 ID |
| `chip_array` | `—` | `group-die` | 芯片材料；原生固定 Silicon (Pure)，DES 无可编辑芯片材料键；内部支持独立选材。 |
| `chip_array` | `k_da` | `group-die-attach` | 芯片粘接材料；名称→材料 ID |
| `chip_array` | `k_encap` | `group-encapsulant` | 塑封材料；名称→材料 ID |
| `chip_array` | `k_wire` | `group-bond-wires` | 键合线材料；名称→材料 ID |
| `chip_array` | `k_mask` | `group-solder-mask` | 阻焊层材料；名称→材料 ID |
| `chip_array` | `k_solder` | `group-bga-solder` | BGA 焊球材料；名称→材料 ID |
| `chip_array` | `k_metal` | `group-metal` | 金属材料；名称→材料 ID |
| `chip_array` | `k_ml` | `group-trace-hole` | 顶层中央区域材料；名称→材料 ID |
| `qfn` | `k_encap` | `group-encapsulant` | 塑封材料；名称→材料 ID |
| `qfn` | `—` | `group-die` | 芯片材料；原生固定 Silicon (Pure)，DES 无可编辑芯片材料键；内部支持独立选材。 |
| `qfn` | `k_da` | `group-die-attach` | 芯片粘接材料；名称→材料 ID |
| `qfn` | `k_dap` | `group-exposed-pad` | DAP 材料；名称→材料 ID |
| `qfn` | `k_lead` | `group-lead-frame` | 引线框材料；名称→材料 ID |
| `qfn` | `k_bw` | `group-bond-wires` | 键合线材料；名称→材料 ID |
| `qfn` | `k_solder` | `group-solder` | 焊料材料；名称→材料 ID |
| `qfn` | `k_land` | `group-thermal-land` | 散热焊盘材料；名称→材料 ID；模板可选，未纳入原生预设材料绑定。 |
| `pqfp` | `k_encap` | `group-encapsulant` | 塑封材料；名称→材料 ID |
| `pqfp` | `—` | `group-die` | 芯片材料；原生固定 Silicon (Pure)，DES 无可编辑芯片材料键；内部支持独立选材。 |
| `pqfp` | `k_da` | `group-die-attach` | 芯片粘接材料；名称→材料 ID |
| `pqfp` | `k_metal` | `group-lead-frame` | 引线框材料；名称→材料 ID |
| `pqfp` | `k_bw` | `group-bond-wires` | 键合线材料；名称→材料 ID |
| `pqfp` | `k_land` | `group-thermal-land` | 散热焊盘材料；名称→材料 ID |
| `pqfp` | `k_sd` | `group-thermal-solder` | 焊料材料；名称→材料 ID |
| `sop` | `k_encap` | `group-encapsulant` | 塑封材料；名称→材料 ID |
| `sop` | `—` | `group-die` | 芯片材料；原生固定 Silicon (Pure)，DES 无可编辑芯片材料键；内部支持独立选材。 |
| `sop` | `k_da` | `group-die-attach` | 芯片粘接材料；名称→材料 ID |
| `sop` | `k_metal` | `group-lead-frame` | 引线框材料；名称→材料 ID |
| `sop` | `k_bw` | `group-bond-wires` | 键合线材料；名称→材料 ID |
| `sop` | `k_land` | `group-thermal-land` | 散热焊盘材料；名称→材料 ID |
| `sop` | `k_sd` | `group-thermal-solder` | 焊料材料；名称→材料 ID |
| `sop` | `kdf` | `group-die-flag` | 芯片承载台材料；名称→材料 ID |

## 焊球布局与附件

适用于 `chip_array`、`cbga_fc`、`pbga_fc`、`pbga_wb`。下表字段位于 `ProjectDocument.Bga`，不在 `Values` 中。

| DES 字段 / 附件 | Bga 内部键 | 转换规则与边界 |
| --- | --- | --- |
| `radio_BGA_modeling` | `representation` | 3→discrete，4→equivalent；WB PBGA 还支持 2→isotropic。Chip Array 内部仅支持 discrete，其 DES 无该键。 |
| `depop_center` | `solder_removal_enabled` | CHECKED→true，UNCHECKED→false。 |
| `MDp`、`MEp` | `populated_columns`、`populated_rows` | 分别为外围满布列数与行数；不是中心删除列数与行数。 |
| `central_balls` | `center_solder_enabled` | CHECKED→true，UNCHECKED→false。 |
| `MDc`、`MEc` | `center_solder_columns`、`center_solder_rows` | 中心阵列 X 列数、Y 行数。 |
| `staggered_matrix` | `staggered` | 主阵列交错排列。 |
| `central_staggered_matrix` | `center_staggered` | 中心阵列交错排列。 |
| `balls` | `omitted_cells` | `列x行:列x行…` 是保留球位；转成 `{row,column}` 的删除名单须取主阵列全集的补集，索引从 0 开始。仅在 depop_center 启用且名单非空时预设转换生效，同时关闭 center_solder_enabled。 |
| `csvBGA` + ZIP 中 `.var2` | `ball_map_enabled` + `ball_map` | `.var2` 为 `id,x,y` CSV；内部点为 `{id,x,y}`，x/y 用 mm。研究工具可构造，PackageCatalog.BallPattern 未自动载入此附件，需显式传入。 |
| FC PBGA ZIP 中 `.var3` | `via_configuration.omitted_cells` 等 | 原生列表是保留通孔，内部为去除配置，需转换；CLI 顶层 `vias` 转入此对象。研究工具有样本，预设适配未自动读入。 |

预设 `BallPattern` 只装配去球开关、满布行列、中心球、交错与 `balls` 补集；`representation` 在未指定时取模板默认值，不能假设 DES 的建模枚举已自动导入。Ball Map 的逐点布局优先于矩阵布局；显式删除名单和 Ball Map 要求离散焊球表达。`omitted_cells.row` 保留原生名单索引语义，生成几何时另有 Y 轴方向换算。

## 金属层表

`Values["metal.layers"]`、`Values["upper.layers"]`、`Values["lower.layers"]` 是 JSON 数组的字符串；行格式为 `[{"depth":0,"thickness":0.018,"coverage":30,"disconnect":false}]`。depth 为从全基板顶面到金属层顶面的距离。

| 家族 / DES 字段 | 内部列 / 规则 |
| --- | --- |
| Chip Array 两层 `tza1,tza2`、`coveragea1,coveragea2` | 首末行 thickness、coverage；首行 depth=0，末行 depth=A2−thickness。 |
| Chip Array 四层 `tz1…tz4`、`coverage1…coverage4`、`z2,z3` | 按原生槽位组成 4 行；中间层 depth 取 z2、z3。 |
| WB PBGA `tz1,tz2,tz3,tz6`、`coverage1,coverage2,coverage3,coverage6`、`z2,z3` | 这些是本仓库样本中的已指定槽位；原生表最多 6 槽。空槽位不创建金属层，不能以 0 厚度补行。两层样本使用首槽 1 与末槽 6；顶底深度自动确定，内层深度取 z2、z3。 |
| WB PBGA `via_con1…via_con6` | 对应有效行的 disconnect；CHECKED→true，UNCHECKED→false。 |
| FC PBGA 芯层 `zi,tzi,coveragei`（i 从 1 开始） | metal.layers 的 depth、thickness、coverage。回放表格 row=0、1，确认保存为 z1/tz1/coverage1、z2/tz2/coverage2；这些键可在已填写表格时出现。 |
| FC PBGA `zb1_i,tzb1_i,coverb1_i` | upper.layers 的 depth、thickness、coverage；同样使用全基板深度。 |
| FC PBGA `zb2_i,tzb2_i,coverb2_i` | lower.layers 的 depth、thickness、coverage；同样使用全基板深度。 |
| 运行预设中的 `depth_m`、`thickness_m` | 乘 1000→内部 depth、thickness；coverage_percent 原值使用，WB 的 disconnect_to_vias→disconnect。DES 示例中的长度数值本身为 mm，不能再次乘 1000。 |

向导 `trace.top_thickness`、`trace.bottom_thickness` 与表格首末行存在共同控制关系。生成器将首层贴顶、末层贴底；内部层位置取表格 depth。切换 `substrate.layers` 会在符合默认值条件时采用原生 four_layer 预设分支，不是简单替换层数标签。

## 未直接映射及需保留语义的 DES 字段

| DES 字段 | 家族 | 处理 / 边界 |
| --- | --- | --- |
| `mDieheat`（及非均匀热源附件） | 全部 | 内部仅支持均匀芯片功率 die.power；无同名热源分区开关。 |
| `radio_bump_modeling`、`radio_C4_modeling` | Bare Die / FC | 凸点固定为有厚度的各向同性等效块；向导的 `bumps.modeling` 只声明 `isotropicCuboid`，不从原生枚举导入，也不把 1/2/4 写进 bumps.array_type。 |
| `radio_TieBar_modeling` | PQFP | 内部无同名字段；连接筋范围见项目决策文档。 |
| `Lbw` | SOP | 原生键合线名义路径长度；内部无独立可编辑键，模型按几何位置确定路径。 |
| `radio_mold`、`p_adhessive`、`k_adhessive`、`k_mold` | FC | 样本包含但无明确内部参数绑定；不凭键名推断分支或材料组。 |
| `k_sadh`、`k_stiff`、`k_sl`、`k_slad`、`kb1`、`kb2` | FC | 有内部材料组语义对应，但未写入 FC 的原生预设材料绑定；见材料表。 |
| 未定义或异常枚举值 | 任一家族 | 非标准外形样本可包含 0 或未初始化整数；不得套用有效建模枚举。应结合原生属性状态、向导及启用分支判断。 |

## 原生属性存在性核实

核实对象为本机 PACK 2504 的 DLL，探测工具逐一校验既定 SHA-256 后读取八类封装的完整数据集、顶盖子对象及向导属性。裸芯片通过本任务最小 DES 加载，其余家族直接使用安装目录 `flocentral/flopack` 的预设。完整数据集、嵌套子对象、向导属性清单、虚函数目标及其指令保存在 [原生启用机制审计](../flotherm_pack_data/native_inspection/pbga_fc_activation.json)，并与归档 DES/FloXML 的 SHA-256 绑定。

| 待核实范围 | 条目数 | 结论 |
| --- | --- | --- |
| Bare Die 的尺寸、功率、翻转、凸点与网格 | 11 | 均有原生属性；无 PackStudio 运行预设绑定。 |
| 七类封装的 footprint.size | 7 | 均有原生向导属性；SOP、PQFP 按子类型使用不同属性名。 |
| FC CBGA / PBGA 的加强环、slug 及 slug 胶层开关 | 6 | 均有原生属性；FC 的 pack_bindings 未绑定这些开关。 |
| FC PBGA 的通孔建模方式 | 1 | 有 modelingOptions.modelCoreViasAs。 |
| Chip Array 的层数与键合线包含开关 | 2 | 有 metalLayers.substrateLayer、wizard.substrateLayer 和 modelingOptions.bondWireModeling。 |
| FC PBGA 的 vias.enabled、upper.enabled、lower.enabled | 3 | 内部独立控制项；PACK 中存在数据组，无一对一可编辑布尔属性。 |

此外，Chip Array/WB PBGA 的通孔启用项来源于原生组状态；metal_layers 是预设编译器展开的行数据，组件实际表格名已在各行标明。组状态、派生数据均不作为 FloSCRIPT 的 property_name。

两种确认方法的证据范围：

- **实际 UI 录制**：在 PACK 的 Macro → Record FloSCRIPT 中创建 Bare Die，修改参数；录制文件直接给出 `die.packagePower`、`die.dieLengthLd`、`die.flippedDie`、`bumpedDie.bumpedDie`、`bumpedDie.numberOfSolderBalls`、`bumpedDie.ballDiameterb`、`bumpedDie.ballHeight` 等组件/属性名称。UI 录制覆盖裸芯片代表项，未声称逐项录制全部家族。
- **原生对象遍历**：直接调用安装 DLL 构造数据集并遍历 Property，确认上表 27 个可对应项的名称；footprint 属性只读取名称、类型与状态，不对其未选中内容调用 DES 序列化函数。
- **FloSCRIPT 回放与保存差分**：23 项标量检查全部通过，修改一个属性后保存 DES，核对目标键及前后差分；覆盖 Bare Die 的 11 个参数、GaAs 材料、两类 FC 的 6 个开关、FC 通孔建模、Chip Array 两项和 QFN 焊盘开关/厚度。另有 FC 芯层金属表的两行回放检查，确认 z/tz/coverage 编号和数值。

例如：`modify_component(name="topCover", property_name="stiffener", new_value="yes")` 保存后仅 `radio_stiffener` 变为 `1`；`modify_component(name="thermalLand", property_name="landThickness", new_value="0.08")` 保存后仅 `ts` 变为 `0.08`。原生属性存在、FloSCRIPT 可写、DES 键存在和 PackStudio 预设已绑定是四种不同结论。

“无独立原生开关”的结论限于本机受哈希校验的 PACK 版本和所枚举的完整数据集/向导；不扩展为其他版本或未公开内部接口的绝对不存在。

## 三个独立启用项的原生机制

| PackStudio 内部项 | 原生组 | 归档可验证的行为 |
| --- | --- | --- |
| `vias.enabled` | `coreVias` | 未指定通孔参数时 groupValid=false，无芯层通孔。参数完整时 groupValid=true；3×4 生成 12 个 core_vias 块，0×0 生成 0 个，二者 isEnabled 都为 true。 |
| `upper.enabled` | `upperBuiltUpRegion` | 未指定区域时 groupValid=false。定义厚度、介质后，即使未定义微通孔数量，仍生成 upper_region；数量 0 或 49 都保留 upper_region，且均生成 microvias1 等效块。 |
| `lower.enabled` | `lowerBuiltUpRegion` | 与上增层相同，输出 lower_region；数量 0 或 49 都保留区域和 microvias2 等效块。 |

本机三个组的虚表 slot 7 均指向 `flopackpackages.dll` RVA `0x22000`，指令为 `mov al,1; ret`。该状态表示恒定可用性。虚表 slot 6 为 `groupValid()`：芯层通孔指向 RVA `0x3a1b0`，上下增层指向 RVA `0x1c010`。`flopackrealise.dll` RVA `0x10ed0` 在分派组 4、6、7 的几何生成前，经 RVA `0x24460` 调用 slot 6；该判断不是读取独立启用属性。

完整数据集及向导清单中没有一对一启用布尔属性；数值未指定、区域参数有效性和孔数量共同决定输出。`groupValid()` 只检查其定义条件，不能替代物理尺寸合法性校验。尤其不能把微通孔数量 0 作为整个增层的关闭标志。

这些判断对应九组独立回放，均包含 `case.json`、可移植 `script.xml`、原生 `model.des`、`model.xml`、`native_run.json` 和 `verification.json`：

- [默认未定义](../flotherm_pack_data/template/pbga_fc/field-activation-default/case.json)、[芯层通孔正常定义](../flotherm_pack_data/template/pbga_fc/field-core-defined/case.json)、[芯层通孔 0×0](../flotherm_pack_data/template/pbga_fc/field-core-zero-count/case.json)。
- [上增层仅区域](../flotherm_pack_data/template/pbga_fc/field-upper-region-only/case.json)、[上增层数量 0](../flotherm_pack_data/template/pbga_fc/field-upper-zero-count/case.json)、[上增层数量 49](../flotherm_pack_data/template/pbga_fc/field-upper-defined/case.json)。
- [下增层仅区域](../flotherm_pack_data/template/pbga_fc/field-lower-region-only/case.json)、[下增层数量 0](../flotherm_pack_data/template/pbga_fc/field-lower-zero-count/case.json)、[下增层数量 49](../flotherm_pack_data/template/pbga_fc/field-lower-defined/case.json)。

## 字段对应的归档证据

- [QFN 焊盘厚度](../flotherm_pack_data/template/qfn/field-land-thickness-0_08/verification.json)：与 0.05 mm 基线相比，0.08 / 0.12 mm 两点分别只改变 DES 的 ts。
- [FC 芯层金属表](../flotherm_pack_data/template/pbga_fc/field-core-metal-baseline/case.json)：两行基线使用 z1/tz1/coverage1、z2/tz2/coverage2；depth、thickness、coverage 三个独立变化点分别只改变 z1、tz1、coverage1。
- [Chip Array 组件层数](../flotherm_pack_data/template/chip_array/field-component-layer-2/verification.json)：修改 metalLayers.substrateLayer，由 2-Layer 到 4-Layer 时只改变 num_metal_layers=2；向导层数初始化仍是另一入口。
- [Bare Die GaAs](../flotherm_pack_data/template/bare_die/field-die-material-gaas/verification.json)：die.dieMaterial=GaAs 保存为 radio_die=2。
- [实际 UI 录制](../flotherm_pack_data/native_inspection/bare_die_ui_record.xml)与[23 项标量差分证据包](../flotherm_pack_data/native_inspection/scalar_replay/manifest.json)：证据包保存原始前后 DES、可移植脚本、实际执行脚本、结果和运行记录；完整文件指纹列在 manifest.json。

## 核对依据

- [参数与材料绑定](../runtime_data/pack_bindings.json)、[八类模板](../runtime_data/templates/)、[原生预设](../runtime_data/presets/)：内部键、原生属性路径、控件和单位。
- [原生 DES 样本](../flotherm_pack_data/template/)：各家族 `baseline/model.des`、`opt_v2_*`、`par_v2_*`、分支和附件用例；枚举值以选项用例与基线差异核对。
- [PackageCatalog.cs](../src/PackStudio.Core/Catalog/PackageCatalog.cs)：AdaptValues、NativeValue、Initialize、BallPattern。
- [ProjectDocument.cs](../src/PackStudio.Core/ProjectDocument.cs)、[RequestDocument.cs](../src/PackStudio.Core/RequestDocument.cs)：Values、Bga、Assignments 的存储和请求字段。
- [DES 容器读取](../tools/floscript/des.py)、[原生预设文本读取](../tools/pack_reference/des.py)、[原生属性编译](../tools/pack_reference/catalog_properties.py)：原始键、状态、单位与表格处理。
- [附件用例](../tools/pack_sweep/cases/attachments.py)、[内层铜深度用例](../tools/pack_sweep/cases/metal_depth.py)：保留坐标转删除名单、CSV 和层表字段。
- [焊球生成](../src/PackStudio.Core/Geometry/SolderBalls.cs)、[金属层生成](../src/PackStudio.Core/Geometry/MetalLayers.cs)、[材料解析](../src/PackStudio.Core/Catalog/MaterialLibrary.cs)：内部表示与消费规则。
- [均匀热源范围](decisions/仅支持均匀芯片热源.md)、[SOP 键合线路径](decisions/原生bug-SOP键合线线长参数.md)、[QFP 连接筋](decisions/QFP连接筋建模选项.md)。
