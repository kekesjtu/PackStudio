# PackStudio

参考 Flotherm PACK 的界面与建模逻辑，通过参数向导生成八类 IC 封装热分析模型，输出 PackStudio XML 给下游网格与求解软件。

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
| `src/PackStudio.Core/` | 领域契约、创建初始化、八类封装生成、前后校验与 PackStudio XML 输出 |
| `src/PackStudio.Cli/` | 研究工具使用的 C# 命令行入口 |
| `runtime_data/` | 封装定义（参数、字段约束与展示配置）、342 个完整方案预设与材料库 |
| `output_format/packstudio/` | 自定义 XML 格式契约与示例 |
| `tests/PackStudio.Tests/` | 几何、材料、功率、参数分支与输出契约回归 |
| `tests/PackStudio.Desktop.Tests/` | 桌面创建、参数编辑、问题定位与模型展示回归 |
| `tests/research/` | 原生研究工具测试 |
| `tools/` | 独立 Python 研究与参考数据维护工具 |
| `flotherm_pack_data/` | 原生扫参、导出、截图和验证结果 |

## 文档

需求、架构与决策见 [docs 文档路由](docs/README.md)。

[运行数据](runtime_data/README.md) · [模型 XML 契约](output_format/packstudio/README.md) · [开发与研究工具](tools/README.md) · [PACK 扫参](tools/pack_sweep/README.md) · [FloSCRIPT](FLOSCRIPT.md)
