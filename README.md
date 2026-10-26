# PackStudio

参考 Flotherm PACK 的界面与建模逻辑，通过参数向导生成 IC 封装热分析模型，
并输出 FloXML，交给下游软件完成网格划分和数值求解。

## 功能

- 八类封装：Chip Array、Bare Die、Flip Chip CBGA、Flip Chip PBGA、PQFP、QFN、SOP、Wirebond PBGA。
- 按封装组件组织的参数向导，提供外形预设、几何参数、材料属性和芯片功率输入。
- 三维矩形块预览、父子模型树、组件检查和递归显示/隐藏。
- 材料库浏览、当前方案物性编辑，以及参数保存与恢复。
- FloXML 文件下载；Windows 独立窗口提供原生保存对话框。

功能范围以 [requirements.md](requirements.md) 为准。
相对 PACK 的主动功能取舍只有[决策索引](docs/decisions/README.md)列出的三项；
其中 bumps 的 Isotropic Cuboid 要求与现有实现尚未对齐。

## 快速开始

需要 uv、Node.js 22.12+ 与 npm。在仓库根目录运行：

```powershell
.\start.ps1
```

脚本安装锁定依赖、准备前端并启动本地服务，随后打开浏览器。
按 `Ctrl+C` 结束服务。前端热更新使用 `.\start.ps1 -Dev`。
首次运行需要下载依赖和由 uv 管理的 Python。

Windows 独立窗口需要 .NET 10 SDK 与 WebView2 Runtime：

```powershell
npm run desktop
```

## 项目结构

| 路径 | 内容 |
| --- | --- |
| `src/frontend/` | React / TypeScript 参数向导与三维界面 |
| `src/packstudio/` | Python API、领域模型、封装生成器和 FloXML 导出器 |
| `src/webview2/` | WPF / WebView2 独立窗口 |
| `default_parameters/` | 运行时模板、原生预设与材料库 |
| `output_format/floxml/` | FloXML 契约、XSD 和示例 |
| `tests/` | 后端、前端、启动和桌面验证 |
| `tools/` | 开发、打包与原生验证工具 |
| `docs/` | 当前决策、开发说明和验证数据 |
| `archive/` | 停用格式的只读参考归档 |
| `flotherm_pack_data/` | 本地原生参考数据，不进入分发包或 Git |
| `tmp/` | 临时产物与日志 |

## 文档与验证

[文档入口](docs/README.md) · [开发说明](docs/development.md) ·
[技术栈](docs/tech_stack.md) · [参数库](default_parameters/README.md) ·
[FloXML 契约](output_format/floxml/README.md)

```powershell
uv run --locked pytest
uv run --locked ruff check .
npm run lint
npm test
npm run build
```
