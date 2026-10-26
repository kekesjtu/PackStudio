# 技术栈与架构

## 数据流

React 参数向导通过本地 HTTP API 提交参数；FastAPI 校验输入并调用封装生成器，
返回统一的物理块模型。前端用同一模型显示三维预览与模型树，FloXML 导出器输出文件。

依赖方向为 `api → templates → domain ← exporters`。
接口层处理协议，模板模块负责几何和等效物性，领域层校验模型，导出器负责格式映射。

## 组件

| 层次 | 技术 | 职责 |
| --- | --- | --- |
| 界面 | React、TypeScript、Material UI | 参数向导、材料编辑和模型检查 |
| 三维 | Three.js、React Three Fiber、Drei | 矩形块预览、选择与显隐 |
| 前端构建 | Vite、npm | 开发服务、资源构建与依赖锁定 |
| 服务 | Python 3.13、FastAPI、Uvicorn | 本地 API 与静态资源托管 |
| 领域 | Pydantic、NumPy | 参数校验、几何和材料计算 |
| 输出 | lxml | FloXML 序列化与开发期 XSD 校验 |
| Windows 窗口 | WPF、.NET 10、WebView2 | 托管页面、文件保存和后端生命周期 |
| 后端分发 | PyInstaller | 携带 Python、服务代码和运行参数库 |
| 质量 | pytest、Ruff、Vitest、Testing Library、ESLint | 回归测试、静态检查和格式检查 |

准确依赖版本以 `uv.lock`、`package-lock.json` 和 .NET 锁文件为准。
Python 解释器由 `.python-version` 固定，使用 uv 管理仓库 `.venv`。

## 数据与部署

`default_parameters/` 是生产运行数据来源，与安装目录和研究资料解耦。
前后端交换 JSON；生成后的物理块包含几何、材料、热源和组件层级。
当前预览和导出使用轴对齐矩形块，内部长度单位为 mm，FloXML 长度单位为 m。

浏览器模式由启动脚本管理前后端；独立窗口加载自身启动的本地后端和前端产物，
关闭窗口时清理其服务进程。运行包不需要 Node、uv 或独立 Python。

## 决策与维护入口

- [架构决策](decisions/采用-Web-前后端分离架构.md)
- [运行数据决策](decisions/JSON运行参数与参考数据解耦.md)
- [桌面宿主决策](decisions/WebView2独立宿主.md)
- [开发与打包](development.md)
