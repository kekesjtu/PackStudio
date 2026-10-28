# 开发与验证

PACK 原生 XML 扫参、DES 导出和本地参考库重建见
[原生扫参与参考库](pack_sweep/README.md)。

## 环境

需要 uv、Node.js 22.12+ 和 npm。Python 版本以 `.python-version` 为准。
解释器与仓库 `.venv` 由 uv 管理，依赖由锁文件固定。

```powershell
uv sync --locked --python-preference only-managed
npm ci
```

添加 Python 依赖用 `uv add`，开发依赖用 `uv add --dev`。
修改声明后运行 `uv lock`，审核并提交 `uv.lock`。

## 浏览器运行

```powershell
.\start.ps1
.\start.ps1 -Dev
.\start.ps1 -Check -NoBrowser
.\start.ps1 -Setup
.\start.ps1 -BackendPort 18000 -FrontendPort 15173
```

默认准备前端生产构建后打开浏览器；`-Dev` 启用热更新。
`-Setup` 刷新依赖并强制构建。切换启动模式前，先在原终端按 `Ctrl+C`。
默认浏览器地址为 `http://127.0.0.1:5173`，API 位于 `http://127.0.0.1:8000`。
健康检查为 `/api/health`，交互式 API 文档为后端 `/docs`。
启动日志位于 `tmp/startup/`。

手动运行时分别在两个终端执行：

```powershell
uv run --locked python -m uvicorn packstudio.api.app:app --reload
npm run dev
```

## Windows 独立窗口

开发需要 .NET 10 SDK 和 WebView2 Runtime。

```powershell
npm run desktop
.\tools\start_webview2.ps1 -BuildOnly
```

默认后端端口为 18080，可用 `-Port 18081` 指定或 `-Port 0` 自动分配。
日志位于 `%LOCALAPPDATA%\PackStudio\WebView2\backend.log`。

## 打包

```powershell
npm run package:desktop
.\tools\package_webview2.ps1 -OutputDirectory release/webview2-next
```

默认产物是 `release/webview2/`，运行 `PackStudio.WebView2.exe`。
分发时携带整个目录；目标机需要 .NET Desktop Runtime 10 和 WebView2 Runtime。
单独打包后端可运行 `npm run package:backend`。

## 验证

```powershell
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
npm run lint
npm test
npm run test:startup
npm run build
npm run test:desktop
```

桌面验证检查实际页面、WebGL、八类生成和 FloXML 下载、原生保存、宿主消息、
端口冲突与进程清理，需要 Windows 桌面会话和相应运行时。

源预设的生成与 FloXML 审计：

```powershell
uv run --locked python -m tools.validate_catalog_presets
```

该命令实际生成模型，检查材料和几何引用、BGA 数量以及 FloXML XSD，默认输出汇总。
需要保留机器报告时，显式传入 `--report tmp/YYYY-MM-DD-catalog-audit/report.json`。

## 临时文件

关闭开发和测试进程后，先预览再清理：

```powershell
.\tools\clean_workspace.ps1 -ListOnly
.\tools\clean_workspace.ps1 -WhatIf
.\tools\clean_workspace.ps1
```

默认保留环境、依赖、分发包与启动日志。删除分发包需显式添加 `-IncludePackages`。
验证数据、运行参数和本地原生参考资料按各自用途维护。
