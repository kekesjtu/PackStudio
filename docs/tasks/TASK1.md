# TASK1 — 技术栈选型与项目初始化

## 状态

已完成（2026-07-11）。

## 目标

搭建 PackStudio 的 目录和文档框架，完成技术栈选型和长期开发计划。

## 子任务

### 1.1 技术栈选型

完成技术栈选型，创建文档 `docs/tech_stack.md`，内容包括：
1.前端使用的技术栈
2.后端使用的技术栈
3.每个技术栈对应的作用

### 1.2 项目脚手架

1. 配置目录结构和基础文档。
2. 配置 python 开发环境。使用 conda activate PackStudio 进入虚拟环境。

### 1.3 Flotherm PACK 参考

1.阅读/figures/references/Flotherm_PACK.md 以及相关图片，了解 Flotherm PACK 的工作方式和 UI 设计。
2.用文字给出你对于每一个step的理解，描述其功能和作用。填写在Flotherm_PACK.md中。

### 1.4 长期PLAN文档

根据requirements.md，拟定一个长期的开发计划，包含每个阶段的目标和任务。

## 执行记录

- [x] 创建 `docs/tech_stack.md` 并记录前端、后端及各技术职责
- [x] 创建架构 ADR、conda/Python 配置和 React/Vite 最小脚手架
- [x] 阅读并逐步解读 14 张 Flotherm PACK 参考图
- [x] 创建 `docs/PLAN.md`，给出分阶段目标、任务和退出标准
- [x] 更新 README、目录说明、测试命名规范和忽略规则
- [x] 通过 JSON、TOML、YAML、Python 语法、文件行数和 Markdown 本地链接静态校验
- [x] 安装前后端依赖并运行 pytest、Ruff、ESLint、Vitest 和 Vite build
- [x] 生成本次提交说明并执行 `git add`（不执行 `git commit`）
