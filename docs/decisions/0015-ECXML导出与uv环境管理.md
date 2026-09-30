# ADR-0015：ECXML 导出与 uv 环境管理

日期：2026-09-30。状态：采用。

## 背景

需要支持用户提供的 ECXML 格式，并利用本机 PACK 文本资料核对默认值；开发、
启动和桌面打包入口原先依赖 conda，用户要求完全切换为 uv。

## 决策

ECXML 导出器只消费 PackageModel，以物理矩形块生成 SI 坐标的 `solid3dBlock`，
保留材料、块功率和组层级，不复用 PTA 切层、Z 平移和布尔压缩。
同块多热源累加进实体功率，避免重复叠加材料块和无材料源块。
对没有通用字段的面边界/网格预设，界面明确提示，原始值保存在审计注释。
安装 XSD 原样纳入测试契约，生产环境不读取安装目录。

Python 使用 uv 管理的 CPython 3.13.15 和仓库 `.venv`；依赖声明位于 pyproject.toml，
开发工具使用默认 dev 组，PyInstaller 使用 packaging 组，所有组锁在 uv.lock。
日常命令、PowerShell 启动与 Electron 开发启动使用 `uv run --locked`，打包增加
`--group packaging`。启动先 exact sync，防止未声明包成为隐式依赖。
Node.js/前端继续使用 npm 与 package-lock.json。

## 原因及影响

物理块是内部预览/体积的真值，ECXML 的块模型可以直接保持它们而不损失材料或功率。
边界和网格限制显式呈现，避免用户把交换文件误认为完整求解配置。
uv 锁文件让开发与打包的 Python 依赖可复现，删除 environment.yml 和 conda 运行入口，
无需全局环境激活。历史 ADR/TASK 保留原验收记录，并标记 TASK15 的环境更新。

## 验证范围

八类模板 ECXML 通过安装 XSD 校验及逐块坐标/材料/功率核对；前后端回归、启动健康检查
和 PyInstaller 构建已验证。实际 CFD 软件导入仍为下游人工验收。
[uv 官方同步说明](https://docs.astral.sh/uv/concepts/projects/sync/)解释锁定与 exact sync 的行为。
