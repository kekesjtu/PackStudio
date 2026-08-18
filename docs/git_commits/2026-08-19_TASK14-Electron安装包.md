# 提交说明 — 2026-08-19

## 变更概述

完成 TASK14 的桌面打包链路：PyInstaller 后端独立可执行文件 + electron-builder
NSIS 安装包，交付不依赖浏览器的 Windows 安装程序。

## 变更详情

### PyInstaller 后端打包

- 后端以 `packstudio.__main__` 为入口打包为 onedir 独立 exe（`packstudio-backend`），
  排除 Windows 不可用的 uvloop，输出 `release/backend/packstudio-backend/`。
- 产物单独验证：API 与静态托管均 200，`--port` 参数与开发形态一致。

### electron-builder 配置（electron-builder.yml）

- `extraResources`：`release/backend/packstudio-backend` → `resources/backend`，
  `dist/` → `resources/frontend`（后端通过 `PACKSTUDIO_FRONTEND_DIR` 托管）。
- NSIS 向导式安装：`oneClick=false`、允许选择安装目录、每用户安装。
- 输出 `release/desktop`，安装包 `PackStudio-0.1.0-setup.exe`。

### 主进程打包分支

- `main.cjs` packaged 分支 spawn `resources/backend/packstudio-backend.exe`，
  注入 `PACKSTUDIO_FRONTEND_DIR` 指向 `resources/frontend`。

### 工程接线

- npm scripts：`package:backend`、`package:desktop`（unpacked 调试）、`dist`（安装包）。
- `.gitignore` 排除 `build/` 与 `release/` 打包产物。

## 验收确认

- [x] 代码符合开发规范（无死代码、无调试残留、命名清晰）
- [x] PyInstaller 产物 exe 单独运行验证通过
- [x] win-unpacked 版全链路运行验证通过（自动拉起后端、页面 200、退出清理无残留）
- [x] NSIS 安装包构建成功，安装后全链路验收通过
- [x] 相关任务文档已更新

## 备注

首次打包需配置 npmmirror 镜像（`electron_mirror`、`electron_builder_binaries_mirror`），
否则 winCodeSign/NSIS 工具从 GitHub 下载会卡住。安装包暂用 Electron 默认图标与空签名，
正式分发前需补充。
