# PackStudio

IC 封装参数化热仿真模板库 — 通过引导式、参数化方式快速生成典型 IC 封装的等效热分析模型。

## 项目简介

PackStudio 面向 IC 封装热仿真工程师，提供：

- **参数化封装模板**：内置经典封装结构模板
- **引导式建模**：向导式参数输入，降低建模门槛
- **笛卡尔块模型**：自动生成与坐标轴平行的矩形块等效热模型
- **指定格式输出**：输出模型文件，对接下游网格生成与数值求解

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

TASK1 已建立最小可运行脚手架。后续开发顺序见 [docs/PLAN.md](docs/PLAN.md)。当前页面和 API
只用于验证工程链路，尚未实现封装模型生成。

## 参考产品

产品设计参考 Siemens Flotherm PACK 的参数化封装模板与引导式建模流程。截图观察和适用范围
见 [figures/references/Flotherm_PACK.md](figures/references/Flotherm_PACK.md)。功能范围始终以
[requirements.md](requirements.md) 为准。
