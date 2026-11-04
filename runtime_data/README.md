# 运行数据、预设与材料库

生产应用从本目录读取版本化 JSON，运行库随应用分发。运行时不需要 PACK 安装、Python 或 docs/。

## 数据组织

| 路径 | 内容 |
| --- | --- |
| `families.json` | 家族显示名、分组、描述、默认选择、图标与示意图样式 |
| `templates/<family>.json` | 字段、初始化声明、创建选项、栏目/示意图配置、单位/校验、建模选项、材料选择及 DES 符号 |
| `model_groups.json` | 领域模型、模型树与导出共用的分组显示名称及父子关系 |
| `presets/<来源目录>/<预设名>.json` | 342 个内部格式预设，包含默认分支及必要的四层分支，共 416 个分支 |
| `presets/index.json` | 内部家族 ID、预设文件路径、分支列表 |
| `materials/<分类>/<文件>.json` | PACK 内置材料记录 |
| `materials/index.json` | 材料名称、分类、路径 |
| `materials/runtime.json` | 内部材料 ID、别名、颜色与项目补充材料 |

八类模板为 `bare_die`、`cbga_fc`、`pbga_fc`、`pbga_wb`、`chip_array`、`qfn`、`pqfp`、`sop`。
QFN、tsop_conv 等来源目录名用于追溯；预设正文及索引中的 family 使用内部 ID。
Bare Die 没有原生预设，使用模板基线。

字段的 `des_symbol` 是 DES 键字符串、包含 `selector` 与 `cases` 的选择映射，或无直接符号时的 null。
它负责界面符号显示，不承担原生属性寻址或数据转换。没有 DES 键的内部字段仍保留完整定义。

`creation_option` 声明创建窗口展示的选项；`creation_only` 声明仅参与创建初始化与创建校验的输入，不作为主向导或保存方案生成的有效输入。创建后的金属厚度以层表为准。`options_source: "presets"` 从预设目录查询候选，不改写模板 JSON 的 options。

概要栏目通过 steps 中的 fields 声明文档/模板/参数来源、标签、格式、空值显隐与可编辑性。对象字段是结构容器，必须声明默认对象和子字段，运行值即使未启用也须保留对象结构；子字段的值校验按条件执行。

## 预设契约与覆盖

预设版本为 `packstudio.preset/v3`，索引版本为 `packstudio.preset-index/v3`。
每个预设具有 id、family、default_branch、branches 和必要的 source 路径/家族。
分支对象仅包含：

- `values`：以 PackStudio 内部字段名为键的规范化参数；焊球及阵列配置统一使用 `bga.*`，通孔去除位于 `vias.configuration`。
- `material_assignments`：内部材料组 ID 到内部材料 ID 的选择；缺失表示不覆盖模板默认。

值以已核实的原生向导初始化及计算结果为依据。单位、枚举、材料 ID、派生层深度与保留球位补集在提取阶段处理。
预设不包含原生 DLL 类型、属性路径、序列化字符串或完整 DES 源文本。
原生组件及 FloSCRIPT 属性的人工核对入口为 [字段对照表](../docs/DES字段与内部参数对应表.md)及其 [JSON](../docs/DES字段与内部参数对应表.json)。

模板基线提供内部建模设置；所选预设覆盖对应参数，方案输入具有优先级。
Chip Array 与 Wirebond PBGA 的四层分支按模板声明选择初始化字段；显式覆盖值在分支初始化之后合成，包括 null、0、false 与恰好等于默认值的输入。保存的完整参数不再触发初始化回填。
基板层栈初始化不改变 `bga.*` 布局配置。材料选择由模板默认、所选预设及方案 `MaterialAssignments` 依次覆盖；材料显式等效物性具有最终优先级。

未指定和没有数值的不适用项保存 null，界面显示空白；原生保留的数值不因分支禁用而清空。
null、0、false 与缺少字段不互相替代。启用结构缺少必需参数时提示填写。
选材空字符串表示 No Attachment；材料库分类、`*` 选项及缺省材料见 [材料决策](../docs/decisions/材料组与默认材料.md)。

金属层使用真实 JSON 数组，行包含 `depth`、`thickness`、`coverage`、`disconnect`，单位分别为 mm、mm、%、布尔值。
depth 从全基板顶面计量；空槽不生成行。模板基线、预设、方案保存、表格编辑和生成器统一使用数组。
方案采用 `packstudio.project/v3`，v2 文件在读取边界进行显式迁移；内存中的方案及保存输出统一使用 v3。方案由 `Values`、`MaterialAssignments`、`CustomMaterials` 和方案标识组成。布局字段使用 `Values` 中的 `bga.*`，层表直接使用 JSON 数组。
方案与生成请求中的未知顶层字段会返回错误；功率通过 `Values["die.power"]` 或请求的 `overrides["<family>.die.power"]` 设置。
创建时由 Core 根据厚度参数计算层栈；显式提供的层表具有优先级。保存方案的层表按输入参与生成。

材料温度依赖参数保留在材料定义及 FloXML 中；组分混合使用参考值。
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
