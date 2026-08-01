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
- 层级最大网格尺寸；
- 稳态热传递的基础配置。

以下内容由 PTA 的网格和求解阶段生成，PackStudio 不导出：

- `<Mesh>` 以及节点、单元等离散网格实体；
- `Results`；
- `LayerPBResults`；
- `ThermalMaskResults`；
- 温度场、热流场及其他求解派生数据。

`MeshSizeXExpression`、`MeshSizeYExpression` 和 `MeshSizeZExpression` 是求解前的最大网格
尺寸设置，不是网格实体。TASK4 起 PackStudio 会导出这些设置。

## 2. 层顺序与 Z 方向

### 2.1 `Layers` 按顶层到底层排列

**实测 + 样例**：PTA 的 `Layers` 集合应按封装顶层到底层排列。对于当前 Flip Chip
CBGA 模型，正确顺序为：

```text
lid
→ lid interface (TIM)
→ heat slug
→ die interface (TIM)
→ encapsulant top cover（仅启用塑封且没有顶部散热结构时）
→ die / encapsulant upper ring
→ flip-chip bumps / underfill / encapsulant lower ring
→ substrate
→ solder balls / in-array static air
```

塑封与 lid 或 heat slug 同时启用时，不存在 `encapsulant top cover` 层；塑封上环与 die 同层并
止于芯片顶面，后续 TIM 从 die 顶面开始。该差异不改变 PTA 顶层到底层的排序规则。

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

### 4.1 固定 Layer Mode 与顶层块厚特例

**样例**：

- 每个 `Layer` 包含一个 `Blocks` 集合和 `ThicknessExpression`；
- `Block` 通过 `XOffsetExpression`、`YOffsetExpression` 和层内
  `ZOffsetExpression` 定位；
- `Rect` 中的 X/Y 表达式描述块内二维矩形；
- `LengthUnit` 使用 `Mm`；
- PackStudio 只输出连续、无间隙的 Z 层叠。

PackStudio 固定写入：

```xml
<Blocks />
<Layers>...</Layers>
<UseBlockBuildMode>false</UseBlockBuildMode>
```

根级 `Structure/Blocks` 不用于 PackStudio 封装导出。即使布尔压缩收益很大，也不能切换到
Block Build Mode。

**PTA 约束**：只有从顶层到底层序列中的第 1 个 Layer 在设置 `IsTopLayer=true` 后，层内
Block 的 `ThicknessExpression` 才可以与 Layer 的 `ThicknessExpression` 不同。其余层内
每个 Block 必须与所属 Layer 等厚。PackStudio 因此：

- 以所有物理块中最高的起始 Z 作为顶层基面；
- 把该基面以上的块放入第 1 层，并保留各自高度；
- 对顶层以下的跨层块按全局 Z 边界切片；
- 对非顶层块执行导出前断言，拒绝任何块厚与层厚不一致；
- 保持 `TopLayerIndex=0`，且只有第 1 层写入 `IsTopLayer=true`。

这种表达利用顶层块可具有不同 Z 厚度的特性减少切片，同时不把该特例错误应用到普通层。

### 4.2 层内矩形布尔操作

同一个 `Block/AllRects` 可以包含多个二维矩形：

```xml
<Rect>
  <Add_sub>true</Add_sub>
  <!-- 外包络或附加区域 -->
</Rect>
<Rect>
  <Add_sub>false</Add_sub>
  <!-- 从已有加区域中扣除 -->
</Rect>
```

层内 Block 把该二维布尔轮廓沿自身厚度挤出。PackStudio 先合并连续的占用单元，并在“多个
加矩形”和“一个外包络加矩形 + 若干空区减矩形”之间选择操作数更少的精确表达。只合并
同一原始逻辑源、材料、结构、父组和体热源密度的碎片，并逐材料验证压缩前后体积。

### 4.3 导热系数

**样例**：材料的 `DaoreXishu` 支持两种形式：

```xml
<!-- 各向同性 -->
<DaoreXishu>25</DaoreXishu>

<!-- 正交各向异性，顺序为 kx,ky,kz -->
<DaoreXishu>12.5,12.5,34.8</DaoreXishu>
```

密度写入 `Midu`，比热写入 `BiRerong`。

### 4.4 体热源

**样例 + PackStudio 约定**：`TiReyuan` 表示体积热源。PackStudio 接收总功率 W，按块体积
换算为 W/m³：

```text
TiReyuan = power_w / (block_volume_mm3 × 1e-9)
```

## 5. 最大网格尺寸

**样例**：PTA 的 `Layer` 和 `Block` 都包含以下字段，顺序位于 `IsTopLayer` 与
`MetalConversionRate` 之间（块中位于 `MaterialName` 与 `Name` 之间）：

```xml
<MeshSizeXExpression>0.25</MeshSizeXExpression>
<MeshSizeYExpression>0.25</MeshSizeYExpression>
<MeshSizeZExpression>0.2</MeshSizeZExpression>
```

**PackStudio 约束**：层级三个值必须大于 0；块级三个值写 0，表示继承层设置。粗、标准、细
预设分别按每层包络在 XY 方向约分 12、24、40 份，在 Z 方向约分 1、2、4 份。自动化测试
明确允许 `MeshSize*Expression`，但继续拒绝 `<Mesh>` 实体。

### 5.1 多跨度 Z 分层与顶层压缩

八类参考模型包含跨越多个高度区间的基板、封装体、引线框和嵌入结构。导出器先收集所有块
的 Z 起止边界并验证堆叠连续。最高物理起点以上合并为第 1 个顶层 Layer，其中的块保留各自
高度；该平面以下的跨区间矩形块切成逐层片段，每个非顶层片段与 Layer 等厚。随后在每层内
恢复连续矩形和精确加/减轮廓。若存在没有任何结构覆盖的空 Z 区间，导出前直接拒绝。该过程
不改变总体积、材料、热源功率和表面边界语义。

## 6. 热边界

**样例**：PTA 热边界使用以下 DataContract 类型：

| 边界 | XML 类型 |
| --- | --- |
| 固定温度 | `FirstTypeThermalBoundary` |
| 热流 | `SecondTypeThermalBoundary` |
| 对流 | `ThirdTypeThermalBoundary` |

表面通过 `FaceKeys` 定位；Z 表面键包含表面 Z 坐标及其 X/Y 范围。边界坐标必须使用与几何
相同的 Z 平移。

### 6.1 TASK5 当前默认边界

**PackStudio 约束**：导出文件始终具有三层边界覆盖：

1. `OtherThermalBondary` 使用 `ThirdTypeThermalBoundary`，默认 300 K、
   10 W/(m²·K)，接管未单独指定的外表面；
2. `PCB-side equivalent cooling` 作用于焊球接触底面，直接写入用户输入的 PCB 侧换热系数，
   默认 1600 W/(m²·K)；
3. `Top surface cooling` 作用于最高结构顶面，直接写入用户输入的顶部换热系数，默认
   10 W/(m²·K)。

TASK5 起 PCB 和顶部均不再输入总热阻，也不执行 `h = 1 / (R × A)` 面积换算；JSON、领域模型
和 PTA `ConvectionCoefficient` 保存同一个值。PCB 侧 1600 W/(m²·K) 约等于 TASK4 默认
6×6 mm、7×7 焊球模型的 20 K/W 路径对应系数，用于在无 PCB 几何时提供有限主要散热路径，
并不等同于 `RθJB` 或真实流体对流。TI 的封装热指标说明指出，JEDEC 静止空气测试中大部分
热量经测试板散出，且板设计会强烈影响结果；因此正式结果必须用实际 PCB 或实测数据校准。
普通外表面和默认顶部的 10 W/(m²·K) 量级参考 COMSOL 电子芯片冷却示例。

- [TI：Semiconductor and IC Package Thermal Metrics](https://www.ti.com/lit/an/spra953d/spra953d.pdf)
- [COMSOL：Electronic Chip Cooling](https://doc.comsol.com/6.4/doc/com.comsol.help.models.heat.chip_cooling/chip_cooling.html)

## 7. 当前人工验收清单

重新导出 PTA XML 后，应在 PTA GUI 中确认：

- 模型树显示全部预期层，不能只依赖三维几何判断；
- 层从 lid 到 solder balls 排列；
- `TopLayerIndex` 指向唯一的 `IsTopLayer=true` 层；
- 根级 `Blocks` 为空且 `UseBlockBuildMode=false`；
- 除第 1 个顶层 Layer 外，所有层内 Block 厚度均与所属 Layer 厚度一致；
- 高碎片代表模型的层内 `AllRects` 同时包含预期的加矩形和减矩形；
- 标准视图中的 +Z 方向与 PackStudio 的“封装底部到顶部”一致；
- 材料、热源、PCB 侧边界、顶部边界和默认外表面边界存在，两个显式换热系数与 UI 输入一致；
- 每个层的 `MeshSizeX/Y/ZExpression` 均大于 0；
- 文件中没有 `<Mesh>` 网格实体和求解结果节点；
- 执行 PTA 网格生成并完成一次稳态求解，确认没有缺失设置提示。

旧 XML 不会因导出器更新而自动变化，修复后必须重新导出并在 PTA 中重新打开。

## 8. 相关文档

- [PTA 输出示例说明](../output_format/README.md)
- [ADR-0002：Flip Chip CBGA 模型与 PTA 导出约定](decisions/0002-Flip-Chip-CBGA-模型与-PTA-导出约定.md)
- [ADR-0004：TASK4 仿真就绪导出约定](decisions/0004-TASK4-仿真就绪导出约定.md)
- [ADR-0005：TASK5 组合焊球与尺寸预设](decisions/0005-TASK5-组合焊球与尺寸预设.md)
- [ADR-0006：TASK6 八类证据驱动模板](decisions/0006-TASK6-八类证据驱动模板.md)
- [ADR-0013：PTA 全分层矩形布尔建模](decisions/0013-TASK13-PTA全分层矩形布尔建模.md)
- [Flip Chip CBGA / BGA 模板说明](templates/flip-chip-cbga.md)
