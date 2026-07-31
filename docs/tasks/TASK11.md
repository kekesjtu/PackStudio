# TASK11：PTA 根级布尔块与实体压缩

**状态**：已完成（2026-07-31）

## 1. 背景

现有 PTA 导出器只使用 `Layers/Layer/Blocks`：先收集全模型 Z 分界，再把每个物理块切成
全局连续层片；每个 XML `Block` 又只包含一个 `Add_sub=true` 矩形。TASK5 的无重叠矩形
差集因此在 QFN 塑封等结构中展开成上千个 XML 实体。

PTA 格式同时提供根级 `Structure/Blocks`、`UseBlockBuildMode`、块级
`ThicknessExpression/ZOffsetExpression`，以及同一块 `AllRects` 中的加减矩形。它适合表达
具有独立 Z 挤出范围的正交二维布尔轮廓。

## 2. 目标

- PackStudio 增加一等的矩形加/减轮廓与独立 Z 挤出实体。
- 预览和几何校验继续使用确定性、无重叠物理矩形块。
- PTA 导出自动把同一逻辑源的碎片恢复为等价布尔整体。
- 高碎片模型使用根级 Block Build Mode，简单模型继续使用已验证 Layer Mode。
- 不跨材料、结构、父组或体热源密度合并实体。

## 3. 实现

### 3.1 领域表达

- [x] 新增 `RectangleOperation(add, x, y, width, height)`。
- [x] 新增 `RectangularBooleanBlock`，包含材料、结构、父组、独立 `z/thickness`、操作序列
  和来源物理块。
- [x] 布尔序列强制先加后减，不能用减矩形建立空实体。
- [x] 规范化时为每个碎片保存原始逻辑块 ID 和名称。

### 3.2 精确压缩

- [x] 仅合并来自同一原始逻辑块、材料、结构、父组和热源密度的碎片。
- [x] 每个逻辑源只按自身 Z 分界切段，不再受全模型其他结构的 Z 面影响。
- [x] 每个 Z 段建立精确 XY 占用网格并合并相邻单元。
- [x] 在“多个加矩形”和“一个外包络加矩形 + 空区减矩形”之间选择操作数更少者。
- [x] 五类高碎片模板逐材料比较压缩前后体积，误差阈值 `1e-10`。

### 3.3 PTA 双模式

- [x] Block Mode 写入根级 `Structure/Blocks`，每个实体独立写入 Z 偏移、厚度和网格尺寸。
- [x] `AllRects/Rect/Add_sub` 同时支持 `true` 加操作和 `false` 减操作。
- [x] Block Mode 写入 `UseBlockBuildMode=true` 和空 `Layers`。
- [x] 自动模式在至少减少 8 个 XML 实体时选择 Block Mode，否则保留 Layer Mode。
- [x] 模型元数据可用 `pta_geometry_mode=auto|block|layer` 显式控制。

## 4. 默认模板结果

| 模板 | 规范化物理块 | 强制 Layer 的 XML 实体 | 自动模式 XML 实体 | 模式 |
| --- | ---: | ---: | ---: | --- |
| Flip Chip CBGA | 4 | 4 | 4 | Layer |
| Flip Chip PBGA | 4 | 4 | 4 | Layer |
| Wirebond PBGA | 184 | 353 | 53 | Block |
| FBGA / FSBGA | 218 | 287 | 167 | Block |
| QFN | 1664 | 3747 | 318 | Block |
| QFP family | 286 | 856 | 75 | Block |
| SOIC family | 143 | 477 | 30 | Block |
| Bare Die | 1 | 1 | 1 | Layer |

QFN 塑封的 1347 个规范化物理碎片在旧 Layer 路径中会展开为 3421 个 XML 实体，
现在压缩为 5 个独立 Z 段布尔实体。QFN 总 XML 实体减少约 91.5%，导出文本从
9,839,576 字节降为 965,828 字节。物理块仍保留在 PackStudio 模型中供预览、边界和
重叠验证使用。

## 5. 验证

- [x] 环形四矩形精确转换为“外框加 + 中孔减”两个操作。
- [x] 根级块能分别写入不同 `ZOffsetExpression` 和 `ThicknessExpression`。
- [x] QFN 根级实体小于规范化物理块的四分之一，并存在 `Add_sub=false`。
- [x] Wirebond PBGA、FBGA、QFN、QFP、SOIC 逐材料体积保持。
- [x] 原有 Layer Mode、层顺序、网格、边界和非连续层拒绝测试保持通过。
- [x] 后端 485 项、前端 12 项测试通过；Ruff、ESLint 和生产构建通过。

## 6. 可信度边界

- 自动化测试证明 XML 结构、布尔体积和既有 Layer Mode 回归；根级 Block Mode 的最终 PTA
  GUI 导入、网格和稳态求解仍需在目标 PTA 版本做人工验收。
- 布尔压缩减少 XML 实体，不改变热材料等效或求解物理假设。
- 不把不同逻辑引脚、焊球、via 或不同热源密度强行合并。
