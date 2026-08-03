# 提交说明 — 2026-08-03

## 变更概述

基于已回放的 FloSCRIPT/FloXML 单变量数据，系统整理 FloTHERM PACK 重要选项对几何、材料、
方向性、热源和网格的影响，并给出可验证的等效计算公式。

## 变更详情

### 选项建模影响目录

- 新增 `flotherm_pack_data/modeling_option_impacts/`，以一个 UI option 一个文件的形式提供
  39 份说明，覆盖 42 个内部 option 目标。
- 覆盖 8 类模板的初始化、die、顶部结构、bumps、基板、vias、bond wires、leadframe、
  solder-ball 排布、外部热路径和网格选项。
- 每份文档列出内部组件/属性、值域、适用模板、实体增删、材料方向性、选项联动、证据路径
  与 PackStudio 采用边界。

### 精确公式与证据边界

- 给出体积分数、密度、质量加权比热、并联导热率、等面积方柱和阵列包络的通用公式。
- 精确反算 filled via、FBGA approximate via、PBGA/QFN via 等效块、BGA solder-ball 层、
  bumps+underfill、bondwire、leadframe、QFN lead/solder 和中央去球边框等材料参数。
- 将直接导出事实、精确反算、强推断和缺少编辑器/材料 payload 的数据边界分级，避免把
  空 solder-ball map、Non-standard Outline 或 No Attachment 案例误当成完整物理规则。
- 明确记录 PackStudio 不采用 collapsed bumps、isotropic BGA layer、复杂 stagger/map 等
  PACK 分支，以及只在 BGA array 层暴露离散/各向异性选择的产品约束。

### 入口文档

- 更新 `flotherm_pack_data/README.md` 的目录结构与完成状态，链接新的建模影响索引。

## 验收确认

- [x] 39 个 option 文件与索引一一对应
- [x] Markdown 相对链接和证据路径检查通过，缺失数为 0
- [x] 所有 option 文件少于 300 行，最长 91 行
- [x] 关键等效公式已独立重算并与 FloXML 双精度数值一致
- [x] 参考数据全量验证器以只读方式通过
- [x] `git diff --check` 通过
- [x] 未修改生产代码、模板参考数据或输出格式契约

## 备注

未执行 `git commit`。全量验证通过 monkeypatch 输出函数以只读方式运行，未刷新
`validation/report.json`、各模板 validation 文件或时间戳。
