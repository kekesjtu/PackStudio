# 提交说明 — 2026-10-13

## 变更概述

新增可独立运行的 WPF / WebView2 桌面宿主，并根据用户授权删除 Electron，实现面向后续 PTA 集成的桌面入口迁移。

## 变更详情

### WebView2 宿主

- 新增 .NET 10 WPF 窗口，复用现有 React 生产页面和 FastAPI 后端。
- 就绪检查核对服务身份并预热模板；固定默认端口保持参数来源，显式支持自动端口。
- 使用 Windows Job Object 清理自己启动的进程树，覆盖正常关闭及宿主强制终止。
- 限制页面来源，验证网页与原生宿主 ping/pong 消息；尚未接入 PTA 模型应用。
- Blob 导出通过原生保存对话框交付，使用 deferral 避免 WebView2 事件内模态重入。
- 下载路径选择可由宿主注入，使文件落盘能够独立于系统对话框自动验证。

### 开发与交付

- 新增开发启动与运行目录打包脚本、NuGet 锁文件及统一 .NET 构建输出目录。
- 两个 PowerShell 脚本使用 UTF-8 BOM，兼容 Windows PowerShell 5 对中文脚本的读取。
- 默认 npm 桌面启动、打包和验证入口切换到 WebView2。
- 删除 electron/main.cjs、electron-builder.yml 和旧 Electron 专用测试；
  npm 移除 electron / electron-builder，更新锁文件及本机依赖树。
- 保留浏览器版与 Python 建模/导出功能，更新 README、技术栈、TASK23 和 ADR-0024。
- 旧 TASK14 标为历史记录；既有提交记录未删除。

## 验收确认

- [x] 新增生产文件均少于 300 行，无死代码、调试残留或注释掉的实现。
- [x] .NET 构建通过，两个项目的 dotnet format 检查通过。
- [x] 前端构建、ESLint 与 31 项前端测试通过。
- [x] 源码及打包模式实际验证 WebView2 页面、WebGL、八类模型生成/导出、XML 保存、宿主消息、端口冲突与退出清理。
- [x] 默认 npm 桌面测试与 Windows PowerShell 5 构建/打包入口验证通过。
- [x] 输出格式实现未改变；八类 PTA XML 在实际 WebView2 中可生成并解析。
- [x] 相关文档与任务状态更新，提交说明随代码提交。
- [x] git diff --cached --check 通过。

## 验证命令

```powershell
npm run build
npm run lint
npm test
npm run test:desktop
dotnet format src/webview2/PackStudio.WebView2.csproj --no-restore --verify-no-changes
dotnet format tests/webview2/PackStudio.WebView2.Smoke.csproj --no-restore --verify-no-changes
powershell -NoProfile -File tools/start_webview2.ps1 -BuildOnly
npm run package:desktop -- -OutputDirectory release/webview2-final
dotnet run --project tests/webview2/PackStudio.WebView2.Smoke.csproj -c Release --no-build -- release/webview2-final
uv run --locked ruff check src/packstudio/__main__.py
git diff --cached --check
```

## 备注

运行目录包含 Python 与默认参数库，无需 uv、Node 或独立 Python；仍需 .NET Desktop Runtime 10 与 WebView2 Runtime。
本次未实现 Windows 安装器、运行时安装、PTA 自动导入、已有模型合并或 PTA 项目参数回存。
原生界面检查确认四栏布局、三维预览、导出对话框及取消返回。
用户按 Escape 停止 Computer Use 后，未继续原生界面操作；最终点击保存未手动完成，XML 落盘由自动化下载测试确认。
前端构建仍报告大于 500 kB 的资源块，npm 审计报告剩余依赖存在 10 项漏洞；本次未执行无关依赖升级。
锁文件中的 electron-to-chromium 是 Browserslist 所需的浏览器版本数据，不是 Electron 桌面运行时，予以保留。
产物与自动化截图在 release/ 和 tmp/ 下，不纳入 Git。
