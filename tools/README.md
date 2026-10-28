# 开发与研究工具

桌面应用、建模核心和命令行使用 .NET 10 SDK。在仓库根目录执行：

```powershell
dotnet restore PackStudio.slnx --locked-mode
dotnet build PackStudio.slnx -c Release --no-restore
dotnet run --project tests/PackStudio.Tests -c Release --no-build -- .
dotnet run --project tests/PackStudio.Desktop.Tests -c Release --no-build
.\start.ps1
```

命令行与桌面使用相同的建模核心：

```powershell
dotnet run --project src/PackStudio.Cli -- catalog
dotnet run --project src/PackStudio.Cli -- generate request.json model.floxml
```

请求可使用保存的 `.packstudio.json` 方案，或包含 `template_id`、`overrides`、`bga`、`vias` 与 `material_assignments` 的扫参输入。输出通过 FloXML XSD 验证。

## 独立研究工具

Python 解释器与研究依赖由 uv 管理，依赖锁定在 `uv.lock`；生产应用不读取 Python 环境。

```powershell
uv sync --locked
uv run --locked pytest
uv run --locked ruff check tools tests/research
```

[PACK 扫参与参考库](pack_sweep/README.md)负责原生 XML 扫参、DES 导出和参考库重建；[FloSCRIPT](../FLOSCRIPT.md)说明本机原生操作。研究工具通过 `tools/dotnet_core.py` 调用 C# 命令行核心。

临时脚本、日志与中间产物放在 `tmp/YYYY-MM-DD-<task-slug>/`，发布产物放在 `release/`。