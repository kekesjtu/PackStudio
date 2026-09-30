# TASK14：Electron 桌面壳

**状态**：已完成（2026-08-18）

## 1. 背景

MVP 阶段明确不使用 Electron/Tauri 打包（见 [docs/tech_stack.md](../tech_stack.md)），
先验证浏览器 + 本地服务工作流。用户确认需要「不依赖浏览器」的桌面形态后，按
ADR-0001 预留的方向引入 Electron 桌面壳：复用现有 Web 前端与 FastAPI 后端，不改变
前后端分离架构。

## 2. 目标

- 本地 `npm run desktop` 直接打开桌面窗口，不再需要手动起两个服务 + 浏览器。
- Electron 只做两件事：保证本地 FastAPI 后端可用、打开加载后端的窗口。
- 渲染层与 API 同源，前端代码零改动，不引入 CORS 与代理。
- 桌面壳启动失败时给出明确错误并退出，退出时清理后端子进程。

## 3. 实现清单

### 3.1 后端

- [x] 新增 `packstudio.__main__` CLI 入口：`python -m packstudio --port <port>`，
      与 PyInstaller 打包后的启动参数一致。
- [x] `app.py` 在 API 路由之后挂载 `StaticFiles` 托管 `dist/`（`PACKSTUDIO_FRONTEND_DIR`
      可覆盖路径；目录不存在时不挂载，保持纯 API 服务）。

### 3.2 Electron 主进程（electron/main.cjs）

- [x] 端口策略：8000 上已有健康后端则复用；否则找空闲端口拉起子进程。
- [x] 开发版后端解释器探测：`PACKSTUDIO_PYTHON` → `~/.conda/envs/PackStudio/python.exe`
      → PATH 上的 `python`；cwd 固定为仓库根。
- [x] 后端就绪轮询 `/api/health`（30s 超时），超时或启动失败时清理并退出。
- [x] 窗口安全默认：`nodeIntegration=false`、`contextIsolation=true`、`sandbox=true`，
      无 preload、无 IPC（渲染层是纯 Web 页面）。
- [x] `will-quit` 时杀掉后端子进程；窗口全部关闭即退出应用。

### 3.3 工程接线

- [x] `package.json` 增加 `main: electron/main.cjs` 与 `desktop` 脚本。
- [x] 前端构建、后端测试、Ruff 均通过，现有工作流不受影响。

### 3.4 桌面打包（PyInstaller + electron-builder）

- [x] 后端打包为 PyInstaller onedir 独立可执行文件（`packstudio-backend`），入口为
      `packstudio.__main__`，排除 Windows 不可用的 uvloop，`--port` 参数与开发一致。
- [x] `main.cjs` 打包分支：spawn `resources/backend/packstudio-backend.exe`，并通过
      `PACKSTUDIO_FRONTEND_DIR` 把 `resources/frontend`（前端构建产物）交给后端托管。
- [x] `electron-builder.yml`：`extraResources` 布局（backend/frontend 进 resources），
      NSIS 向导式安装（`oneClick=false`、可选安装目录），输出到 `release/desktop`。
- [x] npm scripts：`package:backend`（PyInstaller）、`package:desktop`（unpacked 调试）、
      `dist`（NSIS 安装包）。
- [x] 首次打包需设置镜像（`electron_builder_binaries_mirror` 与 `electron_mirror` 指向
      npmmirror），否则 winCodeSign/NSIS 工具从 GitHub 下载会卡住。

## 4. 验证

- [x] `python -m packstudio --port 9000` 静态托管：`/api/health`、`/`、`/assets/*` 均 200。
- [x] 无后端时 `electron .` 自动拉起 `~/.conda/envs/PackStudio/python.exe` 子进程
      （随机空闲端口 1278），窗口加载后健康检查与首页均 200。
- [x] Electron 退出后后端子进程被连带清理，无残留。
- [x] 后端 505 项测试通过，Ruff 通过，`npm run build` 通过。
- [x] PyInstaller 产物 exe 单独运行：API 与静态托管均 200。
- [x] `npm run package:desktop` 的 win-unpacked 版全链路运行：自动拉起打包后端
      （port 4015）、页面 200、退出清理无残留。
- [x] `npm run dist` 产出 `PackStudio-0.1.0-setup.exe`（138MB），安装后全链路验收通过
      （E:\PackStudio 安装实例：后端 4537 端口、页面 200、退出清理无残留）。

## 5. 可信度边界

- 窗口加载固定端口后不再跟随后端重启；后端意外退出时应用直接退出并提示。
- 渲染层无桌面专用能力（文件读写、系统集成），保持与浏览器版行为一致。
- 安装包未配置图标（使用 Electron 默认图标）与代码签名证书（signtool 空签），正式分发
  前需补充。

> 环境更新（2026-09-30，TASK15）：以上 conda / 全局 python 命令为历史记录。
> 当前统一使用 `uv sync --locked` 与 `uv run --locked`；Electron 开发启动通过 uv 执行，
> 具体命令以根目录 README 和 AGENTS.md 为准。
