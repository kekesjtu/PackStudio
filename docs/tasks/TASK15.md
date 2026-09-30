# TASK15：安装目录默认值调研、ECXML 导出与 uv 迁移

**状态**：已完成（2026-09-30）

## 目标

调研本机 FloTHERM 文本默认值，按用户提供的 ECXML 附件扩展导出格式，
参考已打开的 PACK，并将 Python 开发、启动和打包环境全部切换到 uv。

## 完成清单

- [x] 确认 PID 11212 的 PACK 2504 安装路径，读取 342 份 `.des` 并保存字段和来源哈希。
- [x] 当前 21 个同名非 Bare Die 预设的 42 个芯片 X/Y 值全部匹配；明确其余字段尚未全核验。
- [x] 在 PACK 新建向导复核 CBGA 默认外形、Footprint 和顶部结构，检查后取消向导。
- [x] 区分 `.des`、材料标识、二进制材料库与工程级默认设置，生成调研报告和复现脚本。
- [x] ECXML 导出物理矩形块、组件层级、SI 坐标、各向同性/正交材料和累加块功率。
- [x] API 下载接口与前端格式选择接线；边界/网格限制在界面明确提示，原值保留审计注释。
- [x] 将安装 XSD 作为离线测试契约，并生成 Bare Die 默认示例。
- [x] 建立 uv 管理的 Python 3.13.15、`.venv`、uv.lock，划分 dev / packaging 依赖组。
- [x] 删除 environment.yml；启动脚本、Electron 开发启动和后端打包入口切换为 uv。
- [x] Electron 在 Windows 结束后端进程树，覆盖 uv 及冻结 EXE 的子进程层级。
- [x] 更新 README、AGENTS、需求、技术栈、参考资料命令及历史文档的环境更新说明。
- [x] 生成提交说明；用户后续授权自主 commit 后，已提交为 875fd63。

## 验收证据

- `uv run --locked pytest -q -W error -o cache_dir=tmp/pytest`：525 项通过。
- `uv run --locked ruff check .`、`uv run --locked ruff format --check .`：通过。
- `npm run lint`、`npm test`：通过，17 项前端测试。
- `npm run test:desktop`：1 项真实 uv 后端生命周期测试通过，退出后端口释放。
- `npm run build`：通过；保留既有大 bundle 提示。
- `start.ps1 -Check -NoBrowser -BackendPort 18000 -FrontendPort 15173`：通过，测试服务已清理。
- `npm run package:backend`：由 uv 环境成功构建；spec 文件输出到忽略的 build 目录。
- 独立 EXE：健康检查、静态首页和八类 ECXML 导出/XSD 校验通过，测试进程已清理。
- 浏览器检查：格式选择器默认 PTA，切换 ECXML 后按钮/说明正确。
  [界面截图](../../figures/verification/ecxml-export.png)。
- 本机解释器核对：sys.executable 位于仓库 `.venv`，base_prefix 位于 uv 管理的 Python 目录。

## 范围与后续

XSD/数值核对已完成，实际在 FloTHERM / Icepak 中导入的人工验收仍属于下游验收范围。
ECXML 不应用逐面边界或 PTA 网格预设；未扩大生产尺寸库、未改变生产模板默认值。
旧 TASK/ADR 的 conda 内容为历史验收记录，已追加当前 uv 用法说明。

相关文件：[调研报告](../research/flotherm-installation-defaults.md)、
[ECXML 契约](../../output_format/ecxml/README.md)、
[ADR-0015](../decisions/0015-ECXML导出与uv环境管理.md)、
[提交说明](../git_commits/2026-09-30_ECXML与uv迁移.md)。
