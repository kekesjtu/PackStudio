# 四类 BGA 封装的实际焊球阵列参数规则

日期：2026-10-25。范围：外部 Solder Balls 的实际球位、数量、离散几何及组合优先级。

## 结果与证据

带该组外部焊球阵列的封装有 Chip Array、Wirebond PBGA、Flip Chip PBGA、Flip Chip CBGA。
对四类分别创建全新基线，再将同一组参数写入输入 DES，并明确指定离散输出。
每类 45 组变参，共 180 份离散 FloXML，加四份新基线，共 184 份正式新导出。

全部案例逐项核对原生保存的 DES、球对象名称、中心坐标、尺寸、高度和材料引用。
相同输入下四类的主阵列和中央阵列坐标完全一致；最大坐标/尺寸绝对误差为
`2.220446049250313e-16 mm`。

证据来自真实 PACK 2504 导出及输入/保存 DES，没有使用项目生产几何生成器或 DLL 数值探针
决定阵列公式。验证器中的公式是待验证假设，逐项与原生 XML 对照。
正式采集目录为 `flotherm_pack_data/validation/solder_ball_arrays_2026-10-25-complete/`；
早期探索和重试目录没有混入本次结果。

逐案例坐标、数量、输入、软件指纹和来源 SHA-256 见
[机器可读报告](../validation/solder_ball_arrays_floxml_2026-10-25.json)。

## 封装默认值与表示方式

下表是归档默认预设，不是固定封装常数。换预设会改变默认参数。

| 封装 | 默认预设 | MD×ME | e / mm | b / mm | A1 / mm | 默认表示 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Chip Array | ChipArray_24_4X4mm_0_8 | 5×5 | 0.8 | 0.46 | 0.4 | 离散块 |
| Wirebond PBGA | PBGA_121_15X15mm | 11×11 | 1.27 | 0.75 | 0.6 | 正交等效块 |
| Flip Chip PBGA | PBGAFC_49_6X6mm | 7×7 | 0.8 | 0.5 | 0.4 | 正交等效块 |
| Flip Chip CBGA | CBGAFC_49_6X6mm | 7×7 | 0.8 | 0.5 | 0.4 | 正交等效块 |

默认预设名称中的球数不能代替实际参数计数，例如第一行归档为 25 球。
一个等效区域不代表一个物理焊球；本研究统一使用离散导出核验实际球位。
等效材料物性和区域切分不在本研究范围。

## 1. 普通主阵列：MD、ME、e

以封装平面中心为 x=y=0，采用物理坐标从左到右、从下到上的零基索引：

```text
i = 0 .. MD-1
j = 0 .. ME-1
x(i) = (i-(MD-1)/2)*e
y(j) = (j-(ME-1)/2)*e
```

MD 是 X 方向候选列数，ME 是 Y 方向候选行数；e 是两方向共同的网格间距。
不启用筛选时球数为 MD*ME。偶数行/列仍以原点居中，不需要偏置阵列中心。
中心跨度分别为 `(MD-1)*e`、`(ME-1)*e`；圆形投影包络为该跨度加球直径 b。

封装 D/E 不进入此定位公式。在 Chip Array 归档的 D=3.6/4.4、E=3.6/4.4 四个变参中，
Solder_ball 组件与默认值逐字一致。不同家族本体尺寸不同但本次标准化输入的球位也一致。
换预设会重新初始化参数；单独改变封装尺寸与换预设应区别理解。

## 2. Staggered Matrix：棋盘格筛选

普通网格上的保留条件为：

```text
(i+j) % 2 == 0
```

它删除奇偶性不匹配的球位，不把隔行坐标平移半个间距。
无其他筛选时球数为 `ceil(MD*ME/2)`；仍使用原网格的 e 和中心定位。

| 候选阵列 | 普通球数 | Staggered 球数 |
| --- | ---: | ---: |
| 5×5 | 25 | 13 |
| 4×5 / 5×4 | 20 | 10 |
| 4×6 / 6×4 | 24 | 12 |
| 6×6 | 36 | 18 |

四类封装均验证通过。

## 3. Depopulated Center：MDp、MEp

没有非空显式名单时，中央去球对主阵列应用以下规则。
若 `MDp=MD` 或 `MEp=ME`，去球矩形至少一向宽度为零，不删除主阵列球位。
已验证 5×5 下的 (5,5)、(5,2)、(2,5) 都输出完整 25 球。

其余已验证范围 `0<=MDp<MD`、`0<=MEp<ME`：

```text
rx = floor(MDp/2)
ry = floor(MEp/2)
保留条件：i<rx 或 i>=MD-rx 或 j<ry 或 j>=ME-ry
```

即左右各保留 rx 列，上下各保留 ry 行。没有 Staggered 时：

```text
实际球数 = MD*ME - (MD-2*rx)*(ME-2*ry)
```

奇数输入不会自动拆成一边多一行：例如 5×5 下，MDp=2/3 都对应左右各一列。
MDp=MEp=0 与 1 都会删除全部主阵列；2 与 3 都剩外围 16 球。
本式不应省略前述“某向达到总行列数”的边界处理。

| 5×5 下 MDp、MEp | 实际主阵列球数 |
| --- | ---: |
| 0、0 或 1、1 | 0 |
| 2、2 或 3、3 | 16 |
| 1、3 或 3、1 | 10 |
| 2、4 或 4、2 | 22 |
| 5、5 或 5、2 或 2、5 | 25 |

6×5 下，(2,2)、(3,2)、(2,3)、(3,3) 也有相同几何，均为 18 球。
与 Staggered 同时开启时，保留条件是“外围条件 AND 棋盘格条件”；
5×5、MDp=MEp=2 的 16 个外围球经过 Staggered 后剩 8 个。

## 4. 显式逐球去球：非空保留名单优先

DES `balls` 是保留坐标名单，不是删除名单。其 column 从左向右、row 从上向下。
若名单中存储 (column,row)，换成上述物理索引是 `(i,j)=(column,ME-1-row)`。

非空名单直接定义主阵列球位，取代主阵列的自动中央去球和 Staggered 筛选：

| 同一份 24 球保留名单 | 实际主阵列球数 |
| --- | ---: |
| 单独启用名单 | 24 |
| 同时开启主阵列 Staggered | 24 |
| 同时开启中央去球 MDp=MEp=2 | 24 |

因此没有隐含的“再按交错删一次”或“与中央去球删除集合自动取并集”。
需要两类删除同时生效时，应先算出最终保留名单。空名单则回到普通参数生成，
与启用空 CSV 球位图的含义不同。

## 5. Central Balls：独立中央阵列

开启 Central Balls 后，额外生成一个中心位于原点的 MDc×MEc 阵列。
其位置公式与主阵列相同，只将 MD/ME 换为 MDc/MEc；e、b、A1、焊料选择共用。
MDc/MEc 实际保存为 DES 的 MDc/MEc；FloSCRIPT 的属性名仍带 MDp/MEp 后缀，
不能因该命名就与中央去球参数混用。

中央阵列使用自己的 Staggered 开关，不继承主阵列的开关。
关闭中央 Staggered 时生成 MDc*MEc 个对象；开启时按其局部索引筛选 `(i+j)%2==0`。
例如 3×3 中央阵列为 9/5 个，2×3 为 6/3 个。

中央阵列不会自动取代主阵列内部球位，也不会裁剪到去球空洞或自动去重。
应分别统计导出对象数与不同中心位置数：

| 主阵列与中央阵列 | 导出球对象数 | 不同中心位置数 |
| --- | ---: | ---: |
| 完整 5×5 + 中央 2×2 | 25+4=29 | 29 |
| 完整 5×5 + 中央 3×3 | 25+9=34 | 25 |
| 外围 16 球 + 中央 3×3 | 16+9=25 | 25 |
| 主阵列 Staggered 13 球 + 中央 3×3 | 13+9=22 | 17 |

当主阵列和中央阵列在同一方向的行列数奇偶性相同时，网格可能有相同中心坐标；
奇偶性不同时，该方向相差半个 e。上表“不同中心位置数”只统计坐标重合，
没有据此声称不同中心的球体积一定互不相交。

## 6. b、A1、材料和表示方式

离散 FloXML 每个球是矩形柱，等面积转换为：

```text
size_x = size_y = b*sqrt(pi)/2
size_z = A1
z_bottom = 0
```

改变 b 只改变该柱的横截面；改变 A1 只改变球柱高度及相应封装堆叠高度，
不改变球的 x/y 中心或网格数量。改变 e 则缩放 x/y 球位间距，不改变筛选后的球数。
四类均验证 e=0.8/0.65、b=0.5/0.4、A1=0.4/0.5 的对照。
材料选择提供各球的 material 引用，不是球位筛选参数；本次固定 Sn63/Pb37，未扫描不同材料。

Model Solder Ball Array As 决定离散对象还是等效区域的表达。
归档默认与新离散输出可见，默认一个等效块的家族也能导出多个逐球对象。
本研究不从等效块个数反推物理球数，也未声称各表示分支的等效物性都已验证。

## 7. CSV 球位图边界

`solderBallMap/csvBGA` 是独立的任意坐标导入分支，不是上述 `balls` 网格保留名单。
原 180 例关闭该开关；随后已补充四类各 18 例、共 72 份新 FloXML，
详见 [非空 CSV 球位图验证](csv-solder-ball-map-floxml-2026-10-25.md)。
CSV 开启时直接按文件 ID/X/Y 输出，不受 MD/ME/e、交错、中央去球、显式名单影响，
也不另行生成 Central Balls。关闭 CSV 后恢复本研究的规则网格路径。

## 可执行的生成次序

结合后续 CSV 分支验证，可将实际阵列表达为：

```text
CSV 开启：导出对象 = CSV 列表，不另行生成中央阵列
CSV 关闭：
    主阵列 = 非空显式保留名单
           或 [完整 MD×ME 网格 ∩ 中央去球外围条件 ∩ 主阵列棋盘格条件]
    中央阵列 = 独立 MDc×MEc 网格 ∩ 中央阵列自己的棋盘格条件
    导出对象 = 主阵列对象 + 中央阵列对象（保留重合对象）
```

关闭的条件视为不筛选。实际球位应由这些几何规则计算，不能用另一组件的物性参数代替。

## 复现与限制

```powershell
uv run --locked --no-sync --cache-dir tmp/uv-cache python -m tools.solder_ball_array_probes --installation 'E:/Program Files/Siemens/SimcenterFlotherm/2504' --output 'flotherm_pack_data/validation/solder_ball_arrays_recheck'
uv run --locked --no-sync --cache-dir tmp/uv-cache python -m tools.verify_solder_ball_arrays_floxml --archive 'flotherm_pack_data/validation/solder_ball_arrays_recheck' --output 'tmp/solder_ball_arrays_recheck.json'
```

正式原始数据已存在时，只核验不启动 PACK：

```powershell
uv run --locked --no-sync --cache-dir tmp/uv-cache python -m tools.verify_solder_ball_arrays_floxml
uv run --locked --no-sync --cache-dir tmp/uv-cache ruff check tools/solder_ball_array_probes.py tools/verify_solder_ball_arrays_floxml.py
```

范围为 2504 标准外形/实际芯片或默认顶盖分支；整数尺寸、奇偶性、组合规则由上述样本验证。
没有穷举负值、越界名单、超大中央阵列、异常 CSV 和所有材料组合。
没有修改生产几何、默认参数或产品约束。本任务不对应既有 TASK 文件。
