# PACK 当前选项完整性核对 — 2026-10-18

## 结论与范围

以 `8e36bb4` 为基准核对八类模板。**仍有 11 组参考功能缺口**，其中 WB 背面扩散片会影响
已有默认预设；其余多数是不能从当前 UI/API 进入的编辑或结构分支。另列材料候选范围、
概要元数据两项范围问题，以及已经记录的显式基板分支延期；不把它们全部混称为计算错误。

本次为审查，不改变生产模型、材料库或现有取舍。上一轮已经补齐的凸点焊料、underfill 和
BGA 焊料入口确认存在，但不能据此宣称全部参考选项已经补齐。

核对材料：

- `flotherm_pack_data/templates/*/{ui,template,xml_variations}.json` 与当前参数 JSON/schema。
- `internal_property_registry.json` 的 589 个条目逐项归类；检查 116 张参数/条件/关键下拉截图。
- 对相关缺口读取 117 份归档单变量差异记录；它们是旧 PACK 导出证据，本次没有重新运行 DLL。
- 检查当前生成器和公开请求模型，并复现 WB 默认结构缺失及三个材料候选被拒绝的案例。
- 对照 requirements、ADR5/6/8/9/12/19/22/25/26；“当前没实现”不自动等于“明确决定删除”。

机器记录：[逐项清单及输入指纹](../validation/pack_option_audit_2026-10-18.json)。

## 缺口优先级

| 编号 | 优先级 | 模板/功能 | 当前差距 |
| --- | --- | --- | --- |
| G01 | P1 | Wirebond PBGA 背面扩散片 | 29/36 个原生默认预设启用，当前没有对应结构/底部开孔 |
| G02 | P2 | Chip Array/WB 金属层与 WB 承载台 | 缺少金属选材、层覆盖率、WB Cf；Chip Array 顶层开孔也未开放 |
| G03 | P2 | PQFP/SOP 自定义引线框覆盖率 | 缺少 Yes/No 与百分比，只使用 B/e |
| G04 | P2 | 两类 Flip Chip、WB 的独立 Drop-in Slug | 没有独立结构、支脚、偏移、粘接配置 |
| G05 | P2 | 两类 Flip Chip 顶盖 Stiffener | 没有独立加强环及相关尺寸/材料/胶层 |
| G06 | P2 | 八类模板非均匀芯片发热 | 只有总功率，缺少分区/矩阵热源入口 |
| G07 | P2 | Chip Array Filled Vias | 能读取预设状态并计算，但不能在当前方案中切换 |
| G08 | P2 | Chip Array 键合线数量关系与 Include/Ignore | 两个参考选项均未开放 |
| G09 | P2 | WB Thermal Via Depopulation | 没有热过孔去孔编辑入口 |
| G10 | P2 | QFN 过孔结构 | 只有 ignored 默认结果，无启用、尺寸和阵列字段 |
| G11 | P2 | Bare Die Si/GaAs | 当前白名单仅 Silicon，GaAs 已在库中但不可选 |

优先级表示后续支持顺序；“截图存在、当前缺失”并不证明直接添加表单就能完成物理实现。

## G01：WB 背面扩散片不只是少一个开关

参考：[启用截图](../../flotherm_pack_data/templates/pbga_wb/screenshots/conditional_backside_spreader_on.png)、
`pbga_wb/ui.json → backside_spreader`、
`default_parameters/presets/pbga_wb/PBGA_192_17X17mm.json → branches/default/groups/backsideSpreader`。

原生默认分支 29/36 个 `includeBacksideSpreader=true`。示例 `PBGA_192_17X17mm` 的扩散片为
9.4 × 9.4 × 0.018 mm、铜材料，底部铜层孔也为 9.4 × 9.4 mm。当前实际生成结果没有
spreader 块；`bga/pbga_wb.py:125` 仍生成整片 `bottom-trace`，也没有消费对应孔尺寸。

这会改变去球区内的铜/空气分布和连接关系。`pack-parameter-interactions.md` 已记录此差距，
但未见明确放弃这一结构的专项决策；“完整目录不等于完整几何”也不能证明当前默认拓扑等价。

## G02：金属层与承载台只开放了一部分参数

参考：Chip Array 的 `step_07_metal_layers.png`、WB 的 `step_07_metal_layers.png` 和
`step_04_die_flag_solder_mask.png`；对应 ui.json 均包含材料、层表，WB 另有 `Coverage Cf`。

当前两类模板只有 `trace.top_thickness/bottom_thickness` 可编辑。没有金属组分材料选择、
两层覆盖率、WB `flag.coverage`；Chip Array 还没有 Top Metal Layer Hole 的长宽与材料。
两层生产模型的取舍不能解释“两层本身的覆盖率和金属选材也不能调整”。

`core/wirebond_copper.py:13–26` 从预设读取金属、上下层覆盖率和 Cf；`core/coupled_materials.py:121`
同样从预设读取过孔金属。修改物性可以参与已支持的混合计算，但不等于可以换组分材料或覆盖率。
Chip Array 的铜层仍来自家族 `baseline_materials`，没有相应覆盖率编辑链路。

## G03：PQFP/SOP 的自定义覆盖率不是建模方式切换

参考：两类 `conditional_user_defined_leadframe_coverage*.png` 和 ui.json 的
`User Defined Leadframe Coverage`、`Leadframe Coverage`。两类归档均有 Yes 分支及 36%/44%
单变量导出，差异记录确认材料变化。

当前 `core/leadframe_materials.py:16` 固定使用 `leads.width/leads.pitch`。没有开关或百分比字段。
选择固定的等效 cuboid 表达，不要求同时固定金属覆盖率，因此不能用“仅 BGA 提供表达切换”
将此项排除。也不能用改变引线宽度或间距代替：那会同时改变几何。

## G04：独立 Slug 不能由 Plate 代替

参考：CBGA 和 WB 的 `conditional_drop_in_slug_on.png`、CBGA 的
`conditional_slug_adhesive_on.png`，以及三类 ui/registry 和 `includeSlug=true` 导出记录。

缺少独立 slug 的启用、长宽厚/直径、支脚延伸、偏移、净空、材料与脚下粘接设置。
Flip Chip 的 `cover.type=plate` 是顶面热板，且与 lid/encapsulant 互斥；
`flip_chip/cover.py` 的 `_append_plate` 不能表达带支脚的独立嵌入结构，WB 也没有这个替代入口。

## G05：Lid 的加强环分支缺失

参考：[Stiffener Yes 截图](../../flotherm_pack_data/templates/cbga_fc/screenshots/conditional_top_cover_lid_stiffener_yes_top.png)、
CBGA ui.json 的 `top_cover.variants.lid.stiffener_yes_adds`，以及两类 `stiffener=yes` 归档导出。

当前只有 lid 尺寸和胶层字段，没有 Stiffener 开关、外框/腔体尺寸、材料、胶层厚度和选材。
`group-lid-adhesive` 使用名为 Stiffener Adhesive 的材料，不表示已经创建加强环。
登记表未穷举这里的全部材料控件，因此还额外核对了 ui.json 的嵌套列表。

## G06：非均匀热源缺少完整入口

各类 die 页面均有 Non-uniform Die Heat；Bare Die、PQFP、SOP 还保存 Type 1/Type 2 编辑器截图。
Type 1 是矩形区域坐标/功率表，Type 2 是行列功率矩阵，不是一个额外的总功率标量。

当前请求只有总功率；`core/generator.py:144` 按芯片块体积比例分配体热源。
ADR25 采用体源替代 PACK 面源，是源的厚度表达取舍，不能据此推导已经明确放弃空间非均匀性。
本项需要分区输入、保存与导出语义一起设计；本次只确认入口缺口，不宣称热点精度已经验证。

## G07–G10：过孔和键合线仍有独立控制缺口

- **G07**：Chip Array 的 `conditional_filled_vias_yes.png` 与 `filledVias=yes` 归档显示填孔
  改变 Via 的导热率、密度和比热。当前 `coupled_materials.py` 消费源预设状态，却没有 editable
  字段，也没有在 Yes 状态隐藏/禁用 plating 的前后端条件。这与“基准能生成”是两件事。
- **G08**：`dropdown_bond_wire_count_relation.png`/ui.json 保存 Yes/No，
  `dropdown_bond_wire_modeling.png` 保存 Include/Ignore。两项都有归档分支；当前没有对应
  开关，数量公式绑定球数且始终生成线块。不能把结构 Include/Ignore 当成已舍弃的张量表达。
  No 分支的进一步编辑流程需按归档/新证据核验，本报告不猜测其新增字段。
- **G09**：WB `step_06_thermal_vias.png` 的 Via Depopulation 是热过孔去孔编辑器；当前只有
  规则过孔阵列参数，没有对应 omitted-via 配置。BGA 的 `omitted_cells` 不能操作过孔。
  嵌套去孔表与优先级仍需独立回放，不能直接照搬 BGA 规则。
- **G10**：QFN `conditional_model_vias_discrete.png`、`conditional_model_vias_lumped.png` 和
  ui.json 保存启用后的长度、直径、镀层、节距和行列数。当前 qfn.py 没有过孔生成分支。
  默认 ignored 无变化是正确的默认结果，但不足以说明启用整个结构已被明确放弃。

## G11 与材料范围专项 R01

Bare Die [Die Material 截图](../../flotherm_pack_data/templates/bare_die/screenshots/dropdown_die_material.png)
明确为 Si/GaAs。`Gallium Arsenide` 已在独立材料库中，ID 为 `gallium_arsenide_a43e7270`；
当前 `bare_die.json:216` 的 group-die 只有 silicon，实际请求选择 GaAs 被拒绝。
它不是被移除的 thermal-die 分支。

**R01 需要补充逐组件范围确认**：ADR8 明确采用适用材料白名单，因此本报告不将 PACK 任意
材料组切换或全部 131 种材料不可通选算作错误，也不建议加入没有有效物性的 No Attachment。
但白名单机制本身没有逐项证明所有当前候选子集都完整：

- Bare Die `dropdown_underfill_conductivity_resins_01.png` 和 ui.json 的 resin 清单明确提供
  Cookson-7115 等树脂；上一轮该模板复用了 Flip Chip 的 Others 六项，现有请求仍拒绝 Cookson。
- CBGA 的 ui.json 明列 Alumina 94%/96%、Aluminum Nitride 等陶瓷候选，当前 group-substrate
  仅 Alumina Typical。Aluminum Nitride 已在库中，但请求被白名单拒绝。
- 其他单材料组件也应按适用范围审核，不能以“白名单有声明”替代产品取舍理由。

这些是明确的参考候选差异；除 G11 的专用二选一外，未自动把扩大白名单当作本次已授权修复。

## 已排除及另列的能力

- **明确取舍**：standard outline、actual die；两层生产模型；固定厚 bump 等效层；
  禁止 underfill 开关、规则凸点之外的排列、交错球阵、任意球坐标 map；项目中央/去球规则；
  非 BGA 的表达模式切换；温度参考常量；无网格实体、求解器边界、监控点输出。
- **塑封齐平**：Enable Die Flush 不作为新增缺陷；ADR5 已采用单独塑封保留顶部盖层、淹没芯片
  的语义。若以后要支持齐平，应显式修订该范围。
- **网格**：Localize Grid/网格 region 不按 PACK 原样重放；当前采用最大网格尺寸预设，
  FloXML/ECXML 的目标软件配置边界已写入需求与 ADR25。
- **单位**：原生 slug JSON 还保存 m/cm/mm/micron/in/ft/U/mil。当前按 ADR2 使用统一 mm 的
  领域模型/API，多单位输入换算未开放；它不是额外的封装结构，也不计为独立热模型缺陷。
- **QFN 键合线分段数**：参考归档的 4/6 步确实改变几何与材料，但
  `pack-material-couplings.md` 的 QFN 节已经明确“当前项目保留单步等效包络，没有开放 PACK
  多步离散线选项”，本次按已有范围排除，不仅凭“非 BGA 不切换模式”来排除数值字段。
- **C01 已记录延期**：PBGA FC 的显式 core via/metal stack/上下 built-up，在原生默认中多为
  未赋值或 No Attachment；ADR19 和原生默认值研究已声明采用整体等效基板。应列为后续能力，
  不误报成当前参数丢失或认定给空值填零即可恢复。
- **R02 概要元数据**：Part Number、Vendor、额定 Max Power、最高结温/壳温、Notes 均未提供，
  共 48 个登记条目。它们是产品信息范围问题，不把额定温度误当成已删除的求解器边界条件，
  也不把 Max Power 与当前实际 Package Power 混为一项。

## 复现、覆盖与限制

```powershell
uv run --locked python -m tools.audit_pack_options
uv run --locked ruff check tools/audit_pack_options.py tools/pack_option_rules.py tools/pack_option_probes.py
```

589 个登记条目归类为：267 个已有绑定/入口、36 个项目适配入口、109 个有取舍依据、
98 个缺口条目（归并为 G01–G11）、23 个已知延期条目、48 个概要信息条目、8 个受限材料入口。
**条目数不是独立功能数，也不表示 267 个条目所有选项已全部保真。**

工具保存每条参考位置、选项、当前目标、归类理由、截图路径、相关变体差异和源文件 SHA-256；
材料分支还结合嵌套 ui.json 和专项检查，没有把登记表本身当作完整 UI。
截图检查包括参数面板及关键完整原图；starter 对话框背后显示上一个模板是正常状态，
不能把背景控件归给新建模板。截图底部被截断的内容以 JSON 和其他滚动截图交叉核验。

本次没有重演 PACK GUI/DLL、完整组合或下游热求解，也没有按猜测实现缺口。现有基准/变体测试
只能证明当前支持范围，不能用来证明这些未进入当前 schema 的分支已被覆盖。
