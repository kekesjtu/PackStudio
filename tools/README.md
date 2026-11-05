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
dotnet src/PackStudio.Cli/bin/Release/net10.0/PackStudio.Cli.dll generate request.json model.packstudio.xml
```

请求可使用保存的 `.packstudio.json` 方案，或包含 `template_id`、`overrides` 与 `material_assignments` 的扫参输入；布局覆盖使用 `overrides["<family>.bga.<字段>"]`。输出使用自包含的 [PackStudio XML](../output_format/packstudio/README.md)，仅含矩形块、材料和热源；原生 FloXML XSD 只供独立研究工具使用。请求协议由 CLI 适配器解释，Core 接收规范化领域参数；对象字段以完整 JSON 对象覆盖，不支持点号展开的嵌套叶路径。

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