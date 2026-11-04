# PackStudio

参考 Flotherm PACK 的界面与建模逻辑，通过参数向导生成八类 IC 封装热分析模型，输出 FloXML 给下游网格与求解软件。

采用本机 PTA 的 C# / .NET 10、WPF、CommunityToolkit.Mvvm、HelixToolkit.Wpf、Fluent.Ribbon 和 AvalonDock 技术栈。界面与建模核心在同一进程运行。

## 快速开始

Windows 安装 .NET 10 SDK 后，在仓库根目录运行：

```powershell
.\start.ps1
```

构建与验证：

```powershell
.\build.ps1
dotnet run --project tests/PackStudio.Tests -c Release --no-build -- . layout materials projects
dotnet run --project tests/PackStudio.Desktop.Tests -c Release --no-build -- configuration
```

生成可分发的独立桌面程序：

```powershell
dotnet publish src/PackStudio.Desktop -c Release -r win-x64 --self-contained -o release/PackStudio
```

## 项目结构

| 路径 | 职责 |
| --- | --- |
| `src/PackStudio.Desktop/` | WPF 参数向导、三维预览、模型树与材料编辑 |
| `src/PackStudio.Core/` | C# 领域模型、原生预设、八类封装生成与 FloXML 输出 |
| `src/PackStudio.Cli/` | 研究工具使用的 C# 命令行入口 |
| `runtime_data/` | JSON 模板、342 个内部格式预设与材料库 |
| `output_format/floxml/` | FloXML XSD 与示例 |
| `tests/PackStudio.Tests/` | 几何、材料、功率、参数分支与输出契约回归 |
| `tests/research/` | 原生研究工具测试 |
| `tools/` | 独立 Python 研究与参考数据维护工具 |
| `flotherm_pack_data/` | 原生扫参、导出、截图和验证结果 |

## 文档

[产品需求](docs/requirements.md) · [原生桌面架构](docs/decisions/PTA技术栈与原生桌面架构.md) · [开发与研究工具](tools/README.md) · [运行数据](runtime_data/README.md) · [FloXML 契约](output_format/floxml/README.md) · [FloSCRIPT](FLOSCRIPT.md) · [PACK 扫参](tools/pack_sweep/README.md)

| 决策 | 范围 |
| --- | --- |
| [封装与芯片类型](docs/decisions/封装外形与芯片类型范围.md) | 外形与芯片范围 |
| [BGA 与 Bumps](docs/decisions/BGA与Bumps建模表达.md) | 焊球与凸点表达 |
| [去球与去孔矩阵](docs/decisions/去球与去孔矩阵选择.md) | 矩阵框选、展开层级与写回 |
| [均匀热源](docs/decisions/仅支持均匀芯片热源.md) | 功率分配 |
| [重叠块](docs/decisions/重叠块与警告.md) | 重叠与警告 |
| [QFP 连接筋](docs/decisions/QFP连接筋建模选项.md) | 建模选项 |
| [QFP 连接筋板](docs/decisions/QFP连接筋板输出范围.md) | 输出范围 |
| [FC PBGA 通孔](docs/decisions/原生bug-FC-PBGA通孔等效基体导热率.md) | 基体导热率 |
| [FC Slug 支脚与胶层](docs/decisions/原生bug-FC-Slug支脚与胶层纵向位置.md) | 基板接触与纵向定位 |
| [WB PBGA 通孔](docs/decisions/原生bug-Wirebond-PBGA通孔纵向位置.md) | 纵向定位 |
| [WB PBGA 内层铜](docs/decisions/原生bug-Wirebond-PBGA内层铜纵向位置.md) | 铜层与断开区 |
| [SOP 堆叠](docs/decisions/原生bug-SOP芯片与胶层堆叠.md) | 芯片胶层定位 |
| [SOP 键合线](docs/decisions/原生bug-SOP键合线线长参数.md) | 名义路径长度 |
| [新建封装与导航](docs/decisions/新建封装与向导导航.md) | 创建流程与左侧布局 |
| [数值输入](docs/decisions/数值输入框交互.md) | 单位、箭头与范围 |
| [模型树](docs/decisions/模型树排序与显隐.md) | 层次、排序、选择与显隐 |
| [材料可信度](docs/decisions/材料物性可信度提示.md) | 占位值提示 |
| [材料分组](docs/decisions/材料组与默认材料.md) | 分组选材与默认值 |
| [运行库](docs/decisions/JSON运行参数与参考数据解耦.md) | 分发与来源 |
| [预设与空值](docs/decisions/预设参数来源与空值规则.md) | 原生数据与校验 |
| [预设、方案与四层配置](docs/decisions/预设与方案统一契约及四层配置.md) | 完整方案契约、材料选择与按需四层初始化 |
| [内部字段—DES—PACK](docs/DES字段与内部参数对应表.md) · [JSON](docs/DES字段与内部参数对应表.json) | 八类封装参数、材料、布局与脚本属性核对 |
| [FloXML](docs/decisions/仅保留FloXML输出.md) | 输出契约 |
