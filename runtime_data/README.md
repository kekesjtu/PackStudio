# 运行数据、预设与材料库

生产应用从本目录读取版本化 JSON，运行库随应用分发。运行时不需要 PACK 安装、Python 或 docs/。

## 数据组织

| 路径 | 内容 |
| --- | --- |
| `families.json` | 家族显示名、分组、描述、默认选择、图标与示意图样式 |
| `definitions/<family>.json` | 参数键、类型、单位、枚举、创建属性、初始化声明、Bare Die 基线及材料槽位 |
| `templates/<family>.json` | 标签、控件、栏目、示意图、DES 符号、格式与显示条件 |
| `validation/common.json`、`validation/<family>.json` | 字段及业务检查声明、数值范围、生效条件、严重度和消息；共用声明通过 families 限定适用家族 |
| `model_groups.json` | 领域模型、模型树与导出共用的分组显示名称及父子关系 |
| `presets/<来源目录>/<预设名>.json` | 342 个可直接导入的完整方案预设 |
| `presets/<family>/four_layer.json` | Chip Array、Wirebond PBGA 的四层初始化小契约 |
| `presets/index.json` | 内部家族 ID、完整方案预设文件路径 |
| `materials/<分类>/<文件>.json` | PACK 内置材料记录 |
| `materials/index.json` | 材料名称、分类、路径 |
| `materials/runtime.json` | 内部材料 ID、别名、颜色与项目补充材料 |

八类模板为 `bare_die`、`cbga_fc`、`pbga_fc`、`pbga_wb`、`chip_array`、`qfn`、`pqfp`、`sop`。
QFN、tsop_conv 等来源目录名用于追溯；预设正文的 TemplateId 及索引中的 family 使用内部 ID。
Bare Die 没有原生预设，使用参数定义中的基线。

参数定义中的材料内容仅为槽位、候选及默认材料 ID。固定物性来自 `materials/`，等效物性由生成器按当前参数计算，用户物性覆盖保存在方案的 `CustomMaterials`；参数定义不存储等效材料数值。

`validation/` 统一提供校验声明、严重度及消息模板。`InputValidator` 执行字段和跨字段检查，`ModelValidator` 执行模型检查；复杂公式保留在相应校验算法中。字段可通过 `severity` 和 `messages` 设置诊断，`exclusive_minimum` 表达严格下限，`min_rows`、`max_rows` 表达表格行数限制。计算前提保护仅返回规则编号，由统一生成入口使用相同规则目录生成诊断。

字段的 `des_symbol` 是 DES 键字符串、包含 `selector` 与 `cases` 的选择映射，或无直接符号时的 null。
它负责界面符号显示，不承担原生属性寻址或数据转换。没有 DES 键的内部字段仍保留完整定义。

`creation_option` 声明创建窗口展示的选项；`creation_only` 声明仅参与创建初始化的输入，不作为保存方案生成时的有效输入。创建后的金属厚度以层表为准。`options_source: "presets"` 从预设目录查询候选，不改写参数定义中的 options。创建时保留用户输入，生成前统一执行业务校验。

概要栏目通过 steps 中的 fields 声明文档/模板/参数来源、标签、格式、空值显隐与可编辑性。对象字段的参数定义声明默认对象和子字段；方案原始值按提交保留，生成前根据业务分支检查对象与子字段。

## 完整方案与四层配置

预设与用户保存的方案统一使用 `packstudio.project/v4`，通过相同入口导入；索引版本为 `packstudio.preset-index/v4`。预设 Name 与索引键相同。完整方案包含：

- `SchemaVersion`、`TemplateId`、`Name`：契约版本、家族与方案名称。
- `Values`：以内部字段名为键的方案参数；焊球及阵列配置统一使用 `bga.*`，通孔去除位于 `vias.configuration`。
- `MaterialAssignments`：每个组件材料组到材料 ID 的完整选择，缺少材料组会报错。
- `CustomMaterials`：方案自定义物性及用户明确编辑的等效材料物性。

正文不保存 PresetId、footprint.size、预设分支或原生来源字段。材料库记录仍通过材料 ID 引用。

四层初始化独立使用 `packstudio.four-layer/v1`：`schema_version`、`family` 标识契约，`values` 保存共用设置，`preset_values` 以预设 Name 为键保存散热片尺寸差异。它不是完整方案，不进入普通预设索引。完成创建时，根据最终四层选择按需读取。

值以已核实的原生向导初始化及计算结果为依据。单位、枚举、材料 ID、派生层深度与保留球位补集在提取阶段处理。
预设不包含原生 DLL 类型、属性路径、序列化字符串或完整 DES 源文本。
原生组件及 FloSCRIPT 属性的人工核对入口为 [字段对照表](../docs/DES字段与内部参数对应表.md)及其 [JSON](../docs/DES字段与内部参数对应表.json)。

参数定义中的基线提供 Bare Die 建模设置；选择普通预设时复制其完整方案参数与材料选择，用户输入具有优先级。
Chip Array 与 Wirebond PBGA 的四层配置应用共用设置和具体封装差异；显式覆盖值最后合成，包括 null、0、false 与恰好等于默认值的输入。导入和生成保存方案不触发四层读取或初始化回填。
基板层栈初始化不改变 `bga.*` 布局配置。生成时直接使用方案 MaterialAssignments，不叠加预设材料；材料显式等效物性具有最终优先级。

未指定和没有数值的不适用项保存 null，界面显示空白；原生保留的数值不因分支禁用而清空。
null、0、false 与缺少字段不互相替代。启用结构缺少必需参数时提示填写。
选材空字符串表示 No Attachment；材料库分类、`*` 选项及缺省材料见 [材料决策](../docs/decisions/材料组与默认材料.md)。

金属层使用真实 JSON 数组，行包含 `depth`、`thickness`、`coverage`、`disconnect`，单位分别为 mm、mm、%、布尔值。
depth 从全基板顶面计量；空槽不生成行。模板基线、预设、方案保存、表格编辑和生成器统一使用数组。
兼容 v2、v3 方案在读取边界进行显式迁移，恢复其有效材料选择；内存中的方案及保存输出统一使用 v4。布局字段使用 `Values` 中的 `bga.*`，层表直接使用 JSON 数组。
方案与生成请求中的未知顶层字段会返回错误；功率通过 `Values["die.power"]` 或请求的 `overrides["<family>.die.power"]` 设置。
完成创建时由 Core 根据厚度参数计算层栈，不因输入不合理阻断创建；无法参与运算的派生值留空。显式提供的层表具有优先级。保存方案的层表按输入参与生成。

材料温度依赖参数保留在材料定义及 FloXML 中；组分混合使用参考值。
材料记录使用扁平字段 `name`、`group`、`density_kg_m3`、`specific_heat_j_kg_k`、`emissivity`、`conductivity_w_m_k`、`conductivity_coefficient`、`conductivity_reference_temperature`、`kx_w_m_k`、`ky_w_m_k`、`kz_w_m_k`、`conduct_type` 和 `source`；参考温度单位为 °C。
`conduct_type` 为 0 时使用常数标量导热率，为 1 时使用标量导热率、温度系数与参考温度，为 2 时使用三个方向的导热率；其余存储值不参与该类型计算。导热率、密度和比热要求有限且非负，温度系数与参考温度允许负值。
Bumps 使用有厚度的各向同性等效算法，见 [BGA 与 Bumps](../docs/decisions/BGA与Bumps建模表达.md)。

## 验证与研究

```powershell
dotnet run --project tests/PackStudio.Tests -c Release -- .
dotnet run --project tests/PackStudio.Desktop.Tests -c Release
uv run --locked pytest tests/research
```

核心回归按 catalog、parameters、layout、materials、projects 分组，覆盖模型生成、材料与功率、分支/空值、阵列布局和方案读写。参考数据与文档不作为内容快照或指纹校验对象。
原生扫参、导出与截图位于 `flotherm_pack_data/template/`，入口见 [原生参考库](../tools/pack_sweep/README.md)。
原生研究快照使用独立的 `packstudio.native-preset/v1`，提取必须显式指定运行库外的输出目录。
完整研究记录不是正式运行预设；正式数据的编译、迁移与核对使用任务专属临时目录，不作为产品运行依赖。
本机原生集成检查由 `PACK_NATIVE_INSTALLATION` 指定经过审核的安装，未指定时跳过。
