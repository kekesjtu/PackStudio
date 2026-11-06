# 开发与研究工具

桌面应用、建模核心和命令行使用 .NET 10 SDK。在仓库根目录执行：

```powershell
.\build.ps1
dotnet run --project tests/PackStudio.Tests -c Release --no-build -- . layout materials projects
dotnet run --project tests/PackStudio.Desktop.Tests -c Release --no-build -- configuration
.\start.ps1
```

命令行与桌面使用相同的建模核心：

```powershell
.\build.ps1 -Target Cli
dotnet src/PackStudio.Cli/bin/Release/net10.0/PackStudio.Cli.dll catalog
dotnet src/PackStudio.Cli/bin/Release/net10.0/PackStudio.Cli.dll --presets pbga_wb
dotnet src/PackStudio.Cli/bin/Release/net10.0/PackStudio.Cli.dll --help pbga_wb
dotnet src/PackStudio.Cli/bin/Release/net10.0/PackStudio.Cli.dll generate request.json model.packstudio.xml
```

`catalog` 返回家族 ID 数组，`--presets <template_id>` 返回该家族的预设名称数组。两者均输出 JSON。
`--help <template_id>` 输出以内部参数键索引的 JSON，包含 UI 标签 `label` 和 `des_symbol`。条件符号列出选择字段与各分支。枚举选项、对象子字段和表格列分别列在 `options`、`keys` 和 `columns` 下。

请求可使用保存的 `.packstudio.json` 方案，或使用以下格式。省略顶层 `footprint.size` 时选用家族的默认预设。

```json
{
  "template_id": "qfn",
  "design_name": "QFN Demo",
  "footprint.size": "QFN_12X12_100",
  "overrides": {
    "die.power": 2.5
  }
}
```

`overrides` 直接使用内部键，例如 `bga.columns`。对象和数组按完整值覆盖，例如用数组覆盖 `metal.layers`。材料选择可通过顶层 `material_assignments` 提交。
输出使用自包含的 [PackStudio XML](../output_format/packstudio/README.md)，仅含矩形块、材料和热源。原生 FloXML XSD 供独立研究工具使用。

## 独立研究工具

Python 解释器与研究依赖由 uv 管理，依赖锁定在 `uv.lock`；生产应用不读取 Python 环境。

```powershell
uv sync --locked
uv run --locked pytest
uv run --locked ruff check tools tests/research
```

[PACK 扫参与参考库](pack_sweep/README.md)负责原生 XML 扫参、DES 导出和参考库重建；[FloSCRIPT](../FLOSCRIPT.md)说明本机原生操作。研究工具通过 `tools/dotnet_core.py` 调用显式构建好的 C# CLI；调用过程不检查源码时间戳、不触发构建。源码修改后应先执行 `build.ps1 -Target Cli`。`PACKSTUDIO_CLI_BINARY` 可指定其他构建目录中的 CLI DLL，调用失败会显示标准输出与错误诊断。

`build.ps1` 统一锁定依赖还原与 Release 构建，`-Target` 可选 All、Desktop、Cli；`start.ps1` 委托 Desktop 构建后启动界面。`-ArtifactsPath` 指定构建输出目录，`-Offline` 使用本机缓存并跳过在线漏洞数据查询；离线缓存必须已具备锁定依赖。

临时脚本、日志与中间产物放在 `tmp/YYYY-MM-DD-<task-slug>/`，发布产物放在 `release/`。
