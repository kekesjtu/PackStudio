# TASK13：PTA 全分层矩形布尔建模

**状态**：已完成（2026-08-01）

## 1. 背景

TASK11 为减少 TASK5 矩形差集产生的细碎实体，引入了精确二维加/减轮廓，但在压缩收益较大
时改用根级 `Structure/Blocks` 和 `UseBlockBuildMode=true`。后续确认该 Block Build Mode
不适用于 PackStudio 的 PTA 封装输入，所有模板必须继续使用 `Layers/Layer/Blocks`。

PTA 的层内 Block 仍支持多个 `AllRects/Rect` 布尔操作。Z 向还有一条严格限制：只有第 1 个
顶层 Layer 在设置 `IsTopLayer=true` 后，内部 Block 的厚度才可以与 Layer 厚度不同；其他层
内 Block 必须与所属层等厚。

## 2. 目标

- 八类模板全部使用 PTA Layer Mode，删除根级模式选择。
- 在每个 Layer 内恢复同一逻辑整体的连续矩形，并使用加/减布尔操作压缩孔洞和环形区域。
- 尽量利用第 1 个顶层 Layer 的独立块厚特性，减少顶部结构的 Z 切片。
- 非顶层严格逐层等厚，不把顶层特例扩散到普通层。
- 保持材料体积、热源密度、边界坐标和模型树物理块真值不变。

## 3. 实现清单

### 3.1 层规划

- [x] 新增独立 PTA 层规划器，先验证所有 Z 区间连续且存在物理结构。
- [x] 以最高的物理块起始 Z 作为顶层基面，将其以上几何放入唯一顶层。
- [x] 顶层块共享起始 Z，但按真实高度分组并保留各自 `ThicknessExpression`。
- [x] 顶层以下按全局 Z 边界切片，所有非顶层布尔块厚度严格等于层厚。
- [x] 所有层内块写入 `ZOffsetExpression=0`。

### 3.2 布尔压缩

- [x] 把 Z 起点和厚度纳入布尔兼容键，防止跨不兼容挤出范围合并。
- [x] 同一兼容组内合并连续矩形单元。
- [x] 在多个加矩形与“外包络加 + 空区减”之间选择操作数更少的精确表达。
- [x] 保持逻辑源、材料、结构类型、父组和体热源密度隔离。
- [x] PackStudio 物理模型继续保留无重叠 cuboid，布尔表达仅用于紧凑导出。

### 3.3 PTA 输出

- [x] 根级 `Structure/Blocks` 固定为空。
- [x] `UseBlockBuildMode` 固定为 `false`。
- [x] `Layers` 从顶层到底层排列，`TopLayerIndex=0`，仅首层 `IsTopLayer=true`。
- [x] 删除自动根级模式选择；旧 `pta_geometry_mode=block` 元数据不再改变输出路径。

## 4. 默认模板结果

| 模板 | PackStudio 物理块 | PTA Layer | 层内 XML Block |
| --- | ---: | ---: | ---: |
| Flip Chip CBGA | 4 | 4 | 4 |
| Flip Chip PBGA | 4 | 4 | 4 |
| Wirebond PBGA | 184 | 9 | 63 |
| FBGA / FSBGA | 218 | 9 | 182 |
| QFN | 1664 | 7 | 328 |
| QFP family | 286 | 11 | 124 |
| SOIC family | 143 | 10 | 58 |
| Bare Die | 1 | 1 | 1 |

QFN 相比旧的强制逐碎片 Layer 路径仍从 3747 个 XML Block 降至 328 个，同时保持 7 个
Layer、空根级 Blocks 和 `UseBlockBuildMode=false`。

## 5. 验证

- [x] 相邻矩形精确合并为单个加矩形。
- [x] 四矩形环精确转换为“外框加 + 中孔减”。
- [x] 八类默认导出均使用 Layer Mode，且只有首层允许块厚与层厚不同。
- [x] 人工构造不同高度的顶部块，确认首层保留独立厚度、下层保持等厚。
- [x] 五类高碎片模板逐材料比较 XML 布尔体积与物理块体积。
- [x] 完成后端全量测试、Ruff、前端测试和生产构建。
- [ ] 使用目标 PTA GUI 完成代表模型的导入、网格和稳态求解。

## 6. 可信度边界

自动化测试覆盖 XML 结构、层厚约束、布尔体积和现有导出回归。目标 PTA 版本中的 GUI
导入、网格生成和求解仍需人工验收；在此之前不宣称下游兼容性已经最终闭环。
