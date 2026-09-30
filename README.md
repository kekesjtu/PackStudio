# PackStudio

IC 封装参数化热仿真模板库 — 通过引导式、参数化方式快速生成典型 IC 封装的等效热分析模型。

## 项目简介

PackStudio 面向 IC 封装热仿真工程师，提供：

- **八类证据化模板**：覆盖 Flip Chip CBGA/PBGA、Wirebond PBGA、FBGA/FSBGA、
  QFN、QFP、SOIC 与 Bare Die
- **引导式建模**：向导式参数输入，降低建模门槛
- **原生参数契约**：字段、默认值、条件联动和可编辑范围由版本化 JSON 参数库维护
- **笛卡尔块模型**：自动生成与坐标轴平行的矩形块等效热模型
- **阵列等效建模**：倒装凸点固定采用各向异性等效层，BGA 支持离散或等效表达
- **标准尺寸预设**：八类模板提供 342 个源适配规格和 4 个 Bare Die 规格，选择后自动联动结构级参数
- **材料集中管理**：组件向导只开放适用材料，右侧材料库可浏览并覆盖当前方案的三向物性
- **交互式模型检查**：四栏工作区、可调属性栏，以及可一键收展的父子模型树递归显隐
- **工业软件风格**：深色标题栏、灰色面板、紧凑控件与细边框，保持现有功能和四区工作流
- **可选塑封建模**：独立使用时淹没芯片，与顶盖/slug 组合时露出芯片接触面
- **网格控制预设**：输出层级最大网格尺寸；散热边界交由下游求解软件配置
- **紧凑 PTA 几何**：固定使用层模型，在层内以相邻矩形合并和加/减布尔轮廓减少实体
- **参数持久化**：显式保存当前参数，并在下次进入页面时恢复
- **指定格式输出**：输出 PTA XML 或 ECXML；ECXML 交换几何、材料和功率

## 项目结构

```text
PackStudio/
├── docs/                         # 技术选型、ADR、任务与长期计划
├── figures/references/           # 产品参考图与逐步解读
├── flotherm_pack_data/           # 仅开发期使用的 UI、FloXML、变体与材料参考证据
├── output_format/                # 下游输出示例（接口契约）
├── src/frontend/                 # React/TypeScript 前端
├── src/packstudio/               # Python API、领域、模板和导出器
├── tests/frontend/               # Vitest 组件测试
├── tests/backend/                # pytest 后端测试
├── uv.lock                       # Python 跨平台依赖锁文件
├── .python-version               # uv 管理的 Python 版本
├── package.json                  # 前端依赖与命令
├── pyproject.toml                # Python 包、依赖和工具配置
├── requirements.md               # 产品需求
└── AGENTS.md                     # AI 协作指南
```

## 技术栈

- 前端：React 19、TypeScript、Vite 8、Material UI、React Three Fiber
- 后端：Python 3.13、FastAPI、Pydantic、NumPy、lxml
- 质量：Vitest、Testing Library、pytest、Ruff、ESLint

完整选型和各组件职责见 [docs/tech_stack.md](docs/tech_stack.md)，架构理由见
[ADR-0001](docs/decisions/0001-采用-Web-前后端分离架构.md)。

## 快速开始

### 前置条件

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 22.12+ 与 npm

### 一键启动（推荐）

在仓库根目录运行：

```powershell
.\start.ps1
```

脚本会基于自身位置定位仓库，不依赖用户名或固定安装路径；首次运行时会自动创建
项目 `.venv` 环境（uv 管理的 Python）并安装前端依赖，随后启动前后端并打开浏览器。按 `Ctrl+C` 会同时停止
两个服务。

每次启动都会执行 `uv sync --locked`。依赖声明改变后先运行 `uv lock`；
`-Setup` 同时刷新前端依赖。也可执行启动健康检查或自定义端口：

```powershell
.\start.ps1 -Setup
.\start.ps1 -Check -NoBrowser
.\start.ps1 -BackendPort 18000 -FrontendPort 15173
```

### 手动启动

### 1. 配置 Python 环境

在仓库根目录运行，无需激活全局环境：

```powershell
uv sync --locked --python-preference only-managed
```

Python 3.13.15 由 `.python-version` 固定，uv 自动下载解释器并创建 `.venv`。
`pyproject.toml` 声明依赖，`uv.lock` 固定解析结果；默认安装开发工具，
发布运行可用 `uv sync --locked --no-dev`，后端打包工具单独在 `packaging` 组。
添加依赖使用 `uv add <包>`，开发依赖使用 `uv add --dev <包>`。
依赖变更后更新并审核 `uv.lock`，不要用 pip 手工修改环境。

启动后端：

```powershell
uv run --locked python -m uvicorn packstudio.api.app:app --reload
```

健康检查位于 `http://127.0.0.1:8000/api/health`，交互式 API 文档位于
`http://127.0.0.1:8000/docs`。

### 2. 配置前端

另开终端，在仓库根目录运行：

```powershell
npm install
npm run dev
```

开发界面默认为 `http://127.0.0.1:5173`，`/api` 请求会代理到本地后端。

界面顶部可选择 8 类原生模板。向导步骤按 FloTHERM PACK 的封装组件工作流组织，字段、范围、
尺寸预设和条件联动由 PackStudio 的 JSON 参数库声明；BGA 模板额外提供等效/离散表达、中央
焊球和焊球去除，其他模板不显示 BGA 入口。修改参数、
材料或热源后，点击“生成模型”检查三维矩形块与模型树，选择导出格式后点击“导出 PTA XML”或“导出 ECXML”。
ECXML 使用米制物理矩形块，边界条件与网格控制需在目标软件中重设，详见
[ECXML 格式约定](output_format/ecxml/README.md)。
组件材料在对应向导步骤中从有限候选项选择；右侧材料库用于浏览和编辑当前方案物性。
Flip Chip CBGA 的基准复核、组合焊球规则和坐标约定详见
[Flip Chip CBGA / BGA 模板说明](docs/templates/flip-chip-cbga.md)。

### 3. 桌面壳（不依赖浏览器）

安装 Electron 后可直接以桌面窗口运行，无需浏览器和手动启动服务：

```powershell
npm run desktop
```

窗口会复用 8000 端口上已运行的后端，否则通过
`uv run --locked --no-dev python -m packstudio` 自动拉起后端子进程，退出窗口时
一并清理。桌面壳只是窗口壳：渲染层与浏览器版完全一致，详见
[docs/tasks/TASK14.md](docs/tasks/TASK14.md)。

制作 Windows 安装包（PyInstaller 后端 + electron-builder NSIS）：

```powershell
npm run dist        # 产出 release/desktop/PackStudio-<version>-setup.exe
npm run package:desktop   # 仅出 unpacked 目录（release/desktop/win-unpacked），用于调试
```

首次打包需在用户级 `.npmrc` 配置 npmmirror 镜像（`electron_mirror`、
`electron_builder_binaries_mirror`），避免工具下载卡在 GitHub 源。

### 4. 运行验收命令

```powershell
uv run --locked python -m pytest
uv run --locked python -m ruff check .
uv run --locked python -m ruff format --check .
npm run lint
npm test
npm run test:desktop
npm run build
```

参考数据可在开发期独立复核，但软件运行和部署不需要该目录：

```powershell
uv run --locked python flotherm_pack_data\validation\validate_reference_data.py flotherm_pack_data
```

## 当前进度

TASK1 已建立工程基础，TASK2 已完成首个 Flip Chip CBGA / BGA 参数化模板和 PTA XML
导出，TASK3 已完成四栏工作区、集中材料库和模型树显隐，TASK4 已完成仿真就绪网格/边界
预设及工作区精简，TASK5 已完成组合焊球、基本尺寸预设、直接换热系数、条件塑封接触和
材料库纵向调节。TASK6 完成八类证据核对和首轮实现；TASK7 随后将动态参考适配器替换为
八类手写生产模板、内置材料和原生参数 schema。`flotherm_pack_data` 可以从部署包移除，
Flip Chip CBGA 的复核包络和特殊层约束保持不变。TASK8 将组件材料白名单放入向导，并增加
可编辑材料库、可折叠父子模型树显隐和明确的输入允许范围。TASK9 进一步纠正了首版手写
模板对“运行时解耦”的误解：8 类默认几何与材料由代码逐项转录参考基准，320 个数值单变量
和 54 个 Flip-chip 顶盖分支/变体进入开发期回归，而生产运行仍不读取参考目录。TASK10 将
模板实现按 `core`、BGA、Flip-chip、引线框架和 Bare Die 分类，并删除已被通用向导替代的
不可达前端组件链。TASK11 引入精确矩形布尔压缩；TASK12 进一步按参考 UI
重排中文向导，增加 25 个标准尺寸预设，并把固定 standard outline、actual die、凸点厚
各向异性等效层及 QFP/SOIC 散热焊盘与焊料规则写入生产契约。JEDEC 预设仅保留基准和已
捕获的 FloXML 变体，每项分别声明芯片、塑封体、承载台、阵列或引脚等关联默认值，不使用
全局缩放。TASK13 随后纠正 PTA 几何路径：所有模板固定使用 Layer Mode，只有第一个顶层
允许块厚与层厚不同，其余层严格等厚，并在各层内部保留精确加/减布尔压缩。TASK14 引入
Electron 桌面壳：`npm run desktop` 自动拉起后端子进程并打开桌面窗口，无需浏览器。
后续下游人工验收和交付增强见 [docs/PLAN.md](docs/PLAN.md)。

## 参考产品

产品设计参考 Siemens Flotherm PACK 的参数化封装模板与引导式建模流程。截图观察和适用范围
见 [figures/references/Flotherm_PACK.md](figures/references/Flotherm_PACK.md)。功能范围始终以
[requirements.md](requirements.md) 为准。

本机 PACK 文本默认值调研见 [调研报告](docs/research/flotherm-installation-defaults.md)。
TASK15 完成该调研、ECXML 导出和 uv 迁移；安装资料只用于开发期证据与校验，
生产软件不读取 FloTHERM 安装目录。

TASK16 将默认字段、预设、选材与物性迁入 [default_parameters](default_parameters/README.md)，
保存全部 342 个源预设，运行时独立读取 JSON；TASK18 已将 342 个源全部适配为生产选项，连同 Bare Die 共 346 个。
边界设置、环境请求字段与自动冷却边界已移除；恢复旧保存方案时自动丢弃环境字段。
Agent 可以在完成验收和提交说明后自主 commit，详见 [AGENTS](AGENTS.md)。

TASK17 完成工业软件界面风格调整，保留功能、分区及拖拽分隔条；
[工作区截图](figures/verification/industrial-workspace.png) 展示参数页、三维视图和模型树。

TASK18 将源字段映射、缺值继承、中央/去球区域和 Chip Array 逐球坐标接入运行时；
保留已核验默认基线及所有四区工作流。342 个源的 510 种模型配置通过几何与两种导出检查，
验收明细见 [适配审计](default_parameters/adaptation_report.json)。源名称球数冲突和区域定位
差异会在规格页显示，材料继续使用审核等效张量；新规格尚未逐一完成原生 PACK 对照。
