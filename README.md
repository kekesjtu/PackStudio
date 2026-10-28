# PackStudio

参考 Flotherm PACK 的界面与建模逻辑，通过参数向导生成 IC 封装热分析模型，
并输出 FloXML，交给下游软件完成网格划分和数值求解。

## 功能

- 八类封装：Chip Array、Bare Die、Flip Chip CBGA、Flip Chip PBGA、PQFP、QFN、SOP、Wirebond PBGA。
- 按组件组织参数向导，提供 Bare Die 基线设置、七类原生外形预设及几何、材料和功率输入。
- 三维矩形块预览、父子模型树、组件检查和递归显示/隐藏。
- 材料库浏览与当前方案物性编辑。
- FloXML 文件下载；Windows 独立窗口提供原生保存对话框。

功能范围以 [需求说明](docs/requirements.md) 为准。

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
| `runtime_data/` | 运行时模板、原生预设与材料库 |
| `output_format/floxml/` | FloXML 契约、XSD 和示例 |
| `tests/` | 后端、前端、启动和桌面验证 |
| `tools/` | 开发、打包、通用原生导出与回归辅助工具 |
| `docs/` | 产品需求、设计决策和参考数据 |
| `flotherm_pack_data/` | 本地原生参考数据 |
| `tmp/` | 临时产物与日志 |

## 测试与构建

```powershell
uv run --locked pytest
uv run --locked ruff check .
npm run lint
npm test
npm run build
```

## 文档

[需求说明](docs/requirements.md) · [开发与验证操作](tools/README.md) ·
[运行数据](runtime_data/README.md) · [FloXML 契约](output_format/floxml/README.md) ·
[FloSCRIPT 本机操作](FLOSCRIPT.md) · [验证数据](docs/validation/README.md)

| 决策 | 范围 |
| --- | --- |
| [封装外形与芯片类型](docs/decisions/封装外形与芯片类型范围.md) | Standard Outline 与 Actual Die |
| [BGA 与 Bumps 表达](docs/decisions/BGA与Bumps建模表达.md) | BGA 的离散、等效表达与 Bumps 的 Isotropic Cuboid 约定 |
| [均匀芯片热源](docs/decisions/仅支持均匀芯片热源.md) | 芯片总功率按体积均匀分配 |
| [重叠块与警告](docs/decisions/重叠块与警告.md) | 建模、三维渲染与导出允许重叠块，并返回 warning |
| [QFP Tie Bars 建模选项](docs/decisions/QFP连接筋建模选项.md) | QFP 连接筋的建模选项范围 |
| [QFP 连接筋板输出范围](docs/decisions/QFP连接筋板输出范围.md) | QFP 的 tiebar_plt 几何与输出范围 |
| [原生bug：FC PBGA 通孔等效基体导热率](docs/decisions/原生bug-FC-PBGA通孔等效基体导热率.md) | 各向同性基板使用同值三向导热率参与 Core Vias 等效 |
| [原生bug：Wirebond PBGA 通孔纵向位置](docs/decisions/原生bug-Wirebond-PBGA通孔纵向位置.md) | 通孔上下端面贴合两外层铜的内表面 |
| [原生bug：Wirebond PBGA 内层铜纵向位置](docs/decisions/原生bug-Wirebond-PBGA内层铜纵向位置.md) | 内层铜按 Depth 与自身厚度定位，与对应断开区对齐 |
| [原生bug：SOP 芯片与胶层堆叠](docs/decisions/原生bug-SOP芯片与胶层堆叠.md) | 承载台、芯片胶与芯片连续堆叠，键合线端点联动 |
| [原生bug：SOP 键合线线长参数](docs/decisions/原生bug-SOP键合线线长参数.md) | 精简可编辑线长输入，显示只读名义路径长度 |
| [数值输入框交互](docs/decisions/数值输入框交互.md) | 整数框常显箭头，小数框右侧单位与同排范围提示 |
| [模型树排序与显隐](docs/decisions/模型树排序与显隐.md) | 同级节点按 Z 高度排序、右键递归显隐与层级缩进 |
| [材料物性可信度提示](docs/decisions/材料物性可信度提示.md) | 密度或比热占位值的界面提示 |
| [材料组与默认材料](docs/decisions/材料组与默认材料.md) | 分组联动选材、非空默认材料与缺省材料配置 |
| [前后端架构](docs/decisions/采用-Web-前后端分离架构.md) | React 界面与本地 Python 服务 |
| [运行参数与参考数据](docs/decisions/JSON运行参数与参考数据解耦.md) | JSON 运行库、来源记录与独立分发 |
| [预设参数来源与空值](docs/decisions/预设参数来源与空值规则.md) | 预设取值、空白显示与必填校验 |
| [桌面宿主](docs/decisions/WebView2独立宿主.md) | WPF / WebView2 独立窗口 |
| [FloXML 输出](docs/decisions/仅保留FloXML输出.md) | FloXML 输出契约与验证入口 |
