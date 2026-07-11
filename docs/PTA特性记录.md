# PTA 特性记录

本文记录 PackStudio 对 PTA XML 的已知行为，用作导出器实现、回归测试和人工验收依据。

## 证据标记

| 标记 | 含义 |
| --- | --- |
| **实测** | 已通过 PackStudio 导出文件在 PTA GUI 中实际打开确认 |
| **样例** | 从 `output_format/cases_for_PTA/` 中现有 PTA 文件归纳 |
| **PackStudio 约束** | 当前生成器为保证输出稳定而施加的限制，不一定是 PTA 自身限制 |

## 1. PTA 文件的职责边界

### 1.1 无网格和结果也能打开

**实测**：PTA 可以打开只包含输入模型的 XML，不要求文件预先包含网格或求解结果。

PackStudio 因此只导出：

- 分层矩形块几何；
- 材料、密度和比热；
- 体热源；
- 已启用的热边界条件；
- 稳态热传递的基础配置。

以下内容由 PTA 的网格和求解阶段生成，PackStudio 不导出：

- 所有 `Mesh*` 节点和网格实体；
- `Results`；
- `LayerPBResults`；
- `ThermalMaskResults`；
- 温度场、热流场及其他求解派生数据。

## 2. 层顺序与 Z 方向

### 2.1 `Layers` 按顶层到底层排列

**实测 + 样例**：PTA 的 `Layers` 集合应按封装顶层到底层排列。对于当前 Flip Chip
CBGA 模型，正确顺序为：

```text
lid
→ lid interface (TIM)
→ heat slug
→ die interface (TIM)
→ die
→ flip-chip bumps / underfill
→ substrate
→ solder balls
```

PackStudio 领域模型仍采用标准 XYZ 右手坐标，Z 向上。XML 的层集合顺序只是 PTA 的序列化
约定，不代表领域模型的 Z 方向被反转。

### 2.2 顶层索引与顶层标记必须一致

**实测**：`TopLayerIndex` 是从 0 开始的顶层索引，必须与对应层的 `IsTopLayer=true`
保持一致。当前导出中最高 Z 层排在第一位，因此：

```xml
<TopLayerIndex>0</TopLayerIndex>
```

并且仅第一层写入：

```xml
<IsTopLayer>true</IsTopLayer>
```

初版导出曾按底层到顶层排列，同时将 `TopLayerIndex` 设为 0、最后一层标为顶层。PTA
导入后出现 Z 轴反向。统一层顺序、索引和标记后可避免该问题。

### 2.3 负 Z 坐标需要整体平移

PackStudio 以基板底面中心为原点，BGA 焊球位于负 Z。导出时对所有 Z 坐标增加
`-minimum_z`，使最低表面位于 PTA 的 `z=0`。该操作只做平移，不改变层厚和相对位置。

**样例**：层的 `Name` 是显示名称，不驱动几何坐标。PackStudio 名称中的 `@ <z> mm`
仅用于人工检查。

## 3. 特殊层标记与模型树

### 3.1 特殊标记可能隐藏普通模型树节点

**实测**：当层被标记为以下 PTA 特殊封装类型时，对应层不会显示在普通模型树中，但其
几何仍可能出现在三维视图：

- `IsBottomPackaging=true`：测试中隐藏了焊球层；
- `IsDie=true`：测试中隐藏了芯片层；
- `IsTIM=true`：测试中隐藏了热界面层。

这意味着“三维视图中存在几何”不等于“模型树中存在对应层”。初版文件共有 8 个 XML
层，但 PTA 模型树只显示了 substrate、bumps、heat slug 和 lid 四层。

这些特殊分类可能依赖 PTA 的其他专用封装元数据。PackStudio 当前输出通用矩形块模型，
因此将上述三个标记统一写为 `false`，确保每一层都出现在普通模型树中。结构语义保留在
PackStudio JSON 模型和块名称中。

**实测**：`IsSubstrate=true` 在当前测试文件中不会隐藏 substrate 层，可以保留。

## 4. 几何与材料字段

### 4.1 层和块

**样例**：

- 每个 `Layer` 包含一个 `Blocks` 集合和 `ThicknessExpression`；
- `Block` 通过 `XOffsetExpression`、`YOffsetExpression` 和层内
  `ZOffsetExpression` 定位；
- `Rect` 中的 X/Y 表达式描述块内二维矩形；
- `LengthUnit` 使用 `Mm`；
- PackStudio 当前只支持连续、无间隙的 Z 层叠。

最后一项是 **PackStudio 约束**。当前 PTA 导出器会拒绝不连续的 Z 层，避免隐式层位置与
领域几何不一致。

### 4.2 导热系数

**样例**：材料的 `DaoreXishu` 支持两种形式：

```xml
<!-- 各向同性 -->
<DaoreXishu>25</DaoreXishu>

<!-- 正交各向异性，顺序为 kx,ky,kz -->
<DaoreXishu>12.5,12.5,34.8</DaoreXishu>
```

密度写入 `Midu`，比热写入 `BiRerong`。

### 4.3 体热源

**样例 + PackStudio 约定**：`TiReyuan` 表示体积热源。PackStudio 接收总功率 W，按块体积
换算为 W/m³：

```text
TiReyuan = power_w / (block_volume_mm3 × 1e-9)
```

## 5. 热边界

**样例**：PTA 热边界使用以下 DataContract 类型：

| 边界 | XML 类型 |
| --- | --- |
| 固定温度 | `FirstTypeThermalBoundary` |
| 热流 | `SecondTypeThermalBoundary` |
| 对流 | `ThirdTypeThermalBoundary` |

默认外表面可使用零热流的 `SecondTypeThermalBoundary` 表示绝热。表面通过 `FaceKeys`
定位；Z 表面键包含表面 Z 坐标及其 X/Y 范围。边界坐标必须使用与几何相同的 Z 平移。

## 6. 当前人工验收清单

重新导出 PTA XML 后，应在 PTA GUI 中确认：

- 模型树显示全部预期层，不能只依赖三维几何判断；
- 层从 lid 到 solder balls 排列；
- `TopLayerIndex` 指向唯一的 `IsTopLayer=true` 层；
- 标准视图中的 +Z 方向与 PackStudio 的“封装底部到顶部”一致；
- 材料、热源和已启用边界存在；
- 文件中没有网格和求解结果节点。

旧 XML 不会因导出器更新而自动变化，修复后必须重新导出并在 PTA 中重新打开。

## 7. 相关文档

- [PTA 输出示例说明](../output_format/README.md)
- [ADR-0002：Flip Chip CBGA 模型与 PTA 导出约定](decisions/0002-Flip-Chip-CBGA-模型与-PTA-导出约定.md)
- [Flip Chip CBGA / BGA 模板说明](templates/flip-chip-cbga.md)
