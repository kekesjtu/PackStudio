# 提交说明 — 2026-08-18

## 变更概述

引入 Electron 桌面壳，使 PackStudio 可脱离浏览器以桌面窗口形态运行（`npm run desktop`）。

## 变更详情

### 后端

- 新增 `packstudio.__main__` CLI 入口：`python -m packstudio --port <port>`，
  统一开发与 PyInstaller 打包后的启动参数。
- `app.py` 在 API 路由之后挂载 `StaticFiles` 托管前端构建产物 `dist/`，
  `PACKSTUDIO_FRONTEND_DIR` 可覆盖路径，目录不存在时保持纯 API 服务。

### Electron 主进程（electron/main.cjs）

- 端口策略：8000 已有健康后端则复用，否则找空闲端口拉起子进程。
- 开发版后端解释器探测：`PACKSTUDIO_PYTHON` → PackStudio conda 环境 →
  PATH 上的 `python`，cwd 固定为仓库根。
- `/api/health` 轮询就绪（30s 超时），失败时清理并退出。
- 窗口安全默认（`nodeIntegration=false`、`contextIsolation=true`、`sandbox=true`），
  无 preload、无 IPC；退出时清理后端子进程。

### 工程接线

- `package.json` 增加 `main` 字段与 `desktop` 脚本（`npm run build && electron .`）。

## 验收确认

- [x] 代码符合开发规范（无死代码、无调试残留、命名清晰）
- [x] 后端 505 项自动化测试通过
- [x] Ruff 通过，`npm run build` 通过
- [x] 后端静态托管验证：`/api/health`、`/`、`/assets/*` 均 200
- [x] 无后端时 Electron 自动拉起 conda 环境后端子进程并正常加载窗口
- [x] Electron 退出后后端子进程被清理，无残留
- [x] 相关任务文档已更新

## 备注

PyInstaller 后端独立可执行文件与 electron-builder 安装包（NSIS）尚未制作，属后续任务。
