# PackStudio

IC 封装参数化热仿真模板库 — 通过引导式、参数化方式快速生成典型 IC 封装的等效热分析模型。

## 项目简介

PackStudio 面向 IC 封装热仿真工程师，提供：

- **参数化封装模板**：内置经典封装结构模板
- **引导式建模**：向导式参数输入，降低建模门槛
- **笛卡尔块模型**：自动生成与坐标轴平行的矩形块等效热模型
- **阵列等效建模**：支持焊点离散方柱和正交各向异性等效块
- **材料集中管理**：结构引用共享材料，统一维护三向导热率、密度和比热
- **交互式模型检查**：四栏工作区、可调属性栏和模型树右键显隐
- **可选塑封建模**：以连续分层的无重叠矩形块表达芯片外围塑封体
- **指定格式输出**：输出不含网格和求解结果的精简 PTA XML

## 项目结构

```text
PackStudio/
├── docs/                         # 技术选型、ADR、任务与长期计划
├── figures/references/           # 产品参考图与逐步解读
├── output_format/                # 下游输出示例（接口契约）
├── src/frontend/                 # React/TypeScript 前端
├── src/packstudio/               # Python API、领域、模板和导出器
├── tests/frontend/               # Vitest 组件测试
├── tests/backend/                # pytest 后端测试
├── environment.yml               # PackStudio conda 环境
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

- conda
- Node.js 22.12+ 与 npm

### 一键启动（推荐）

在仓库根目录运行：

```powershell
.\start.ps1
```

脚本会基于自身位置定位仓库，不依赖用户名或固定安装路径；首次运行时会自动创建
`PackStudio` conda 环境并安装前端依赖，随后启动前后端并打开浏览器。按 `Ctrl+C` 会同时停止
两个服务。

依赖文件变更后可强制刷新环境；也可只执行一次启动健康检查或自定义端口：

```powershell
.\start.ps1 -Setup
.\start.ps1 -Check -NoBrowser
.\start.ps1 -BackendPort 18000 -FrontendPort 15173
```

### 手动启动

### 1. 配置 Python 环境

在仓库根目录运行：

```powershell
conda env update --name PackStudio --file environment.yml --prune
conda activate PackStudio
```

首次不存在该环境时可运行：

```powershell
conda env create --file environment.yml
conda activate PackStudio
```

启动后端：

```powershell
python -m uvicorn packstudio.api.app:app --reload
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

界面当前提供唯一的 Flip Chip CBGA / BGA 模板。修改封装、阵列、材料或边界参数后，点击
“生成模型”检查三维矩形块和模型树，再点击“导出精简 PTA XML”。模板参数、阵列模式、
坐标约定和导出内容详见
[Flip Chip CBGA / BGA 模板说明](docs/templates/flip-chip-cbga.md)。

### 3. 运行验收命令

```powershell
conda activate PackStudio
python -m pytest
python -m ruff check .
python -m ruff format --check .
npm run lint
npm test
npm run build
```

## 当前进度

TASK1 已建立工程基础，TASK2 已完成首个 Flip Chip CBGA / BGA 参数化模板和 PTA XML
导出，TASK3 已完成四栏工作区、集中材料库、模型树显隐和可选塑封。当前只支持该模板；后续
开发顺序见
[docs/PLAN.md](docs/PLAN.md)。

## 参考产品

产品设计参考 Siemens Flotherm PACK 的参数化封装模板与引导式建模流程。截图观察和适用范围
见 [figures/references/Flotherm_PACK.md](figures/references/Flotherm_PACK.md)。功能范围始终以
[requirements.md](requirements.md) 为准。
