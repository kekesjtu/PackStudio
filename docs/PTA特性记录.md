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
→ encapsulant top cover（启用塑封时）
→ die
→ flip-chip bumps / underfill
→ substrate
→ solder balls / in-array static air
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

## 6. 热边界

**样例**：PTA 热边界使用以下 DataContract 类型：

| 边界 | XML 类型 |
| --- | --- |
| 固定温度 | `FirstTypeThermalBoundary` |
| 热流 | `SecondTypeThermalBoundary` |
| 对流 | `ThirdTypeThermalBoundary` |

表面通过 `FaceKeys` 定位；Z 表面键包含表面 Z 坐标及其 X/Y 范围。边界坐标必须使用与几何
相同的 Z 平移。

### 6.1 TASK4 默认边界

**PackStudio 约束**：导出文件始终具有三层边界覆盖：

1. `OtherThermalBondary` 使用 `ThirdTypeThermalBoundary`，默认 300 K、
   10 W/(m²·K)，接管未单独指定的外表面；
2. `PCB-side equivalent cooling` 作用于焊球接触底面；用户输入 PCB 到环境的总热阻，导出器
   按目标总面积换算 `h = 1 / (R × A)`；
3. `Top surface cooling` 作用于最高结构顶面，默认沿用外表面对流；启用顶部关键散热面后，
   同样由总热阻换算对流系数。

默认 PCB 到环境热阻 20 K/W 是无 PCB 几何时让模型具备有限主要散热路径的工程初值，并不
等同于 `RθJB`。TI 的封装热指标说明指出，JEDEC 静止空气测试中大部分热量经测试板散出，且
板设计会强烈影响结果；因此 PackStudio 不把纯封装自然对流作为默认的唯一散热路径。自然
对流 10 W/(m²·K) 的量级参考 COMSOL 电子芯片冷却示例。正式结果必须用实际 PCB 或实测
热阻校准。

- [TI：Semiconductor and IC Package Thermal Metrics](https://www.ti.com/lit/an/spra953d/spra953d.pdf)
- [COMSOL：Electronic Chip Cooling](https://doc.comsol.com/6.4/doc/com.comsol.help.models.heat.chip_cooling/chip_cooling.html)

## 7. 当前人工验收清单

重新导出 PTA XML 后，应在 PTA GUI 中确认：

- 模型树显示全部预期层，不能只依赖三维几何判断；
- 层从 lid 到 solder balls 排列；
- `TopLayerIndex` 指向唯一的 `IsTopLayer=true` 层；
- 标准视图中的 +Z 方向与 PackStudio 的“封装底部到顶部”一致；
- 材料、热源、PCB 侧边界、顶部边界和默认外表面边界存在；
- 每个层的 `MeshSizeX/Y/ZExpression` 均大于 0；
- 文件中没有 `<Mesh>` 网格实体和求解结果节点；
- 执行 PTA 网格生成并完成一次稳态求解，确认没有缺失设置提示。

旧 XML 不会因导出器更新而自动变化，修复后必须重新导出并在 PTA 中重新打开。

## 8. 相关文档

- [PTA 输出示例说明](../output_format/README.md)
- [ADR-0002：Flip Chip CBGA 模型与 PTA 导出约定](decisions/0002-Flip-Chip-CBGA-模型与-PTA-导出约定.md)
- [ADR-0004：TASK4 仿真就绪导出约定](decisions/0004-TASK4-仿真就绪导出约定.md)
- [Flip Chip CBGA / BGA 模板说明](templates/flip-chip-cbga.md)
