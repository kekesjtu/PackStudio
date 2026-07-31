# PackStudio

IC 封装参数化热仿真模板库 — 通过引导式、参数化方式快速生成典型 IC 封装的等效热分析模型。

## 项目简介

PackStudio 面向 IC 封装热仿真工程师，提供：

- **八类证据化模板**：覆盖 Flip Chip CBGA/PBGA、Wirebond PBGA、FBGA/FSBGA、
  QFN、QFP、SOIC 与 Bare Die
- **引导式建模**：向导式参数输入，降低建模门槛
- **原生参数契约**：字段、默认值、条件联动和可编辑范围在生产模板中显式维护
- **笛卡尔块模型**：自动生成与坐标轴平行的矩形块等效热模型
- **阵列等效建模**：倒装凸点固定采用各向异性等效层，BGA 支持离散或等效表达
- **基本尺寸预设**：旧版 CBGA 工作区可一次应用 10 个常用 CBGAFC 外形
- **材料集中管理**：组件向导只开放适用材料，右侧材料库可浏览并覆盖当前方案的三向物性
- **交互式模型检查**：四栏工作区、可调属性栏，以及可一键收展的父子模型树递归显隐
- **可选塑封建模**：独立使用时淹没芯片，与顶盖/slug 组合时露出芯片接触面
- **仿真就绪预设**：输出层级最大网格尺寸及默认、PCB 侧和顶部换热系数
- **紧凑 PTA 几何**：高碎片结构自动使用根级独立 Z 布尔块和加/减矩形，减少求解器实体
- **参数持久化**：显式保存当前参数，并在下次进入页面时恢复
- **指定格式输出**：输出不含网格实体和求解结果的 PTA XML

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

界面顶部可选择 8 类原生模板。向导字段、范围和条件联动由 PackStudio 生产代码显式实现；
BGA 模板额外提供等效/离散表达、中央焊球和焊球去除，其他模板不显示 BGA 入口。修改参数、
材料、热源或边界后，点击“生成模型”检查三维矩形块与模型树，再点击“导出 PTA XML”。
组件材料在对应向导步骤中从有限候选项选择；右侧材料库用于浏览和编辑当前方案物性。
Flip Chip CBGA 的基准复核、组合焊球规则和坐标约定详见
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

参考数据可在开发期独立复核，但软件运行和部署不需要该目录：

```powershell
E:\anaconda\Scripts\conda.exe run -n PackStudio python flotherm_pack_data\validation\validate_reference_data.py flotherm_pack_data
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
不可达前端组件链。后续下游人工验收和交付增强见 [docs/PLAN.md](docs/PLAN.md)。

## 参考产品

产品设计参考 Siemens Flotherm PACK 的参数化封装模板与引导式建模流程。截图观察和适用范围
见 [figures/references/Flotherm_PACK.md](figures/references/Flotherm_PACK.md)。功能范围始终以
[requirements.md](requirements.md) 为准。
