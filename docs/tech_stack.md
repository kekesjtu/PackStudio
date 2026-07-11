# PackStudio 技术栈

## 1. 选型结论

PackStudio 采用“浏览器界面 + 本地 Python 服务”的前后端分离架构：

```text
React 参数向导 / 三维预览
              ↓ REST / JSON
FastAPI 参数校验与模型生成
              ↓
统一领域模型（矩形块、材料、热源、边界条件）
              ↓
PTA XML 等下游文件格式
```

该架构把交互展示与热模型规则分开。领域模型和导出器不依赖 UI，后续可以被命令行、
批处理或其他客户端复用。

## 2. 前端技术栈

| 技术 | 基线 | 作用 |
| --- | --- | --- |
| React | 19 | 组织模板选择、分步参数表单、材料配置和导出检查等交互界面 |
| TypeScript | 5.9+ | 为组件属性、API 数据和表单状态提供静态类型检查 |
| Vite | 8 | 开发服务器、热更新、TypeScript 构建和生产资源打包 |
| Material UI | 7 | 提供表单、列表、步骤导航、弹窗和主题能力，快速建立一致的工程 UI |
| Three.js + React Three Fiber | Three.js r180+ / R3F 9 | 将笛卡尔矩形块渲染为可旋转、选取和高亮的三维预览 |
| Vitest + Testing Library | Vitest 4 | 验证组件行为、向导状态和用户可见结果 |
| ESLint | 9 | 检查 TypeScript/React 的常见错误和 Hooks 使用规则 |

选择说明：

- React 适合将每一种封装及其步骤拆成可组合组件，TypeScript 能约束复杂参数对象。
- Vite 8 提供轻量开发服务器和生产构建；其官方要求为 Node.js 20.19+ 或 22.12+，
  项目统一要求 Node.js 22.12+。
- R3F 9 与 React 19 对应，既保留 Three.js 能力，又能让三维对象跟随 React 状态更新。
- Material UI 覆盖 Flotherm PACK 参考界面中大量使用的导航、输入框、选择器和树形信息。

## 3. 后端技术栈

| 技术 | 基线 | 作用 |
| --- | --- | --- |
| Python | 3.13 | 实现参数校验、几何生成、材料计算、输出适配和自动化测试 |
| FastAPI | 0.115+ | 提供本地 REST API，并自动生成 OpenAPI 接口文档 |
| Pydantic | 2.10+ | 定义参数、矩形块、材料、热源和边界条件的领域数据模型及约束 |
| NumPy | 2.1+ | 处理阵列坐标、批量矩形块生成和等效材料属性计算 |
| lxml | 5.3+ | 生成并校验包含命名空间的 PTA XML 文件 |
| Uvicorn | 0.32+ | 运行本地 ASGI 服务 |
| pytest + pytest-cov | pytest 8.3+ | 执行领域规则、API、导出快照和回归测试 |
| Ruff | 0.8+ | 统一 Python 代码检查、导入排序和格式校验 |

后端内部按依赖方向划分：

```text
api → templates → domain ← exporters
```

- `domain` 只包含统一数据模型和不依赖框架的规则。
- `templates` 将封装参数转换为领域模型。
- `exporters` 只消费领域模型，不反向依赖具体模板。
- `api` 负责协议适配，不承载几何或热学业务规则。

## 4. 数据与接口策略

- 前后端交换 JSON，接口契约由 FastAPI/OpenAPI 描述。
- 后端内部以 Pydantic 模型作为唯一可信数据结构，避免 UI 对象直接进入导出器。
- 几何统一表达为与坐标轴平行的矩形块，并显式携带单位、材料、源项和结构类型。
- PTA XML 示例属于外部接口契约；导出实现需要使用黄金文件和结构化对比测试。
- MVP 不引入数据库。内置模板先使用受版本控制的声明式文件；确有用户模板检索、迁移需求时，
  再评估 SQLite。

## 5. 开发和发布工具

| 工具 | 作用 |
| --- | --- |
| conda `PackStudio` 环境 | 固定 Python 3.13 和 Python 依赖入口 |
| npm | 管理前端依赖并生成锁文件 |
| `pyproject.toml` | 集中声明 Python 包、依赖、pytest 和 Ruff 配置 |
| `environment.yml` | 创建或更新同名 conda 环境 |
| `.editorconfig` | 统一编码、换行和缩进 |
| Git 功能分支 | 隔离功能开发；长任务仅暂存，不由 Agent 自动提交 |

本地基线于 2026-07-11 核对：`PackStudio` 环境为 Python 3.13.14，Node.js 为
22.15.0，均满足脚手架要求。

## 6. 当前明确不采用的技术

- 不采用 CAD/B-Rep 内核：当前需求只需要轴对齐矩形块，复杂 CAD 内核会增加不必要的模型语义。
- 不在本项目引入网格器或求解器：它们属于需求明确排除的下游模块。
- MVP 不使用 Electron/Tauri 打包：先验证浏览器 + 本地服务工作流；确有离线安装包需求时再做 ADR。
- MVP 不部署云端服务，也不引入账号、权限和多租户系统。

## 7. 官方资料

- [React 中使用 TypeScript](https://react.dev/learn/typescript)
- [Vite 入门与 Node.js 要求](https://vite.dev/guide/)
- [Material UI 概览](https://mui.com/material-ui/getting-started/)
- [React Three Fiber 介绍与版本对应关系](https://r3f.docs.pmnd.rs/)
- [FastAPI 功能与 OpenAPI/Pydantic 支持](https://fastapi.tiangolo.com/features/)
- [Pydantic Models](https://docs.pydantic.dev/latest/concepts/models/)
- [NumPy 文档](https://numpy.org/doc/stable/)
- [conda 环境管理](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html)
- [pytest 入门](https://docs.pytest.org/en/stable/getting-started.html)
- [Ruff 文档](https://docs.astral.sh/ruff/)
- [Vitest 入门](https://vitest.dev/guide/)
