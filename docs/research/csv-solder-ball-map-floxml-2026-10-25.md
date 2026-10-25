# 非空 CSV Solder Ball Map：四类封装原生 FloXML 验证

日期：2026-10-25。补充此前实际焊球阵列研究中未覆盖的非空任意坐标球位图分支。

## 结果

Chip Array、Wirebond PBGA、Flip Chip PBGA、Flip Chip CBGA 各 18 组变参，
共 72 份新离散 FloXML，加四份新基线，共 76 份正式新导出。
逐例输入回读、球位图载荷、对象名称、坐标、尺寸、高度和材料引用全部核验通过。
四类相同输入的球位完全一致；最大坐标/尺寸误差为 `2.220446049250313e-16 mm`。

**开启 CSV Solder Ball Map 后，主焊球按 CSV 的 ID、X、Y 直接生成；
规则网格、交错、中央去球、显式网格名单和 Central Balls 均不再决定这一分支的输出。**
这不只是主阵列坐标覆盖，Central Balls 也不会另行生成。
关闭 CSV 开关后，已保存的 CSV 载荷被忽略，恢复原有规则网格/显式名单路径。
后续 [非离散模式验证](equivalent-solder-ball-rules-floxml-2026-10-25.md) 进一步确认，
请求非离散模式并开启 CSV 时，原生保存模式会切回离散，仍逐球输出纯焊料。

逐例输入、保存后载荷、实际坐标、数量、原生软件指纹、文件 SHA-256 见
[机器可读验证报告](../validation/csv_solder_ball_map_floxml_2026-10-25.json)。

## 真实 CSV 导入与载荷发现

使用 computer-use 技能操作独立的 PACK 验证窗口，加载新建的 Chip Array 测试文件，
通过 Solder Ball Map → Click To Edit → Import File 导入以下 CSV：

```csv
ID,X,Y
A1,-1.1,0.3
B2,0.25,-0.7
C3,1.4,0.8
```

编辑器显示三行，列头为 ID、X Coord (mm)、Y Coord (mm)。导入后点 OK 并保存验证 DES。
原先打开的 Wirebond PBGA 方案只做了只读查看并取消，没有写入测试数据。
源格式确认后关闭了本次创建的验证窗口。

原生 DES 是 ZIP，普通 `.des` 成员仅有 `csvBGA=CHECKED`，真实坐标保存在同名 `.var2` 成员：

```text
A1,-1.100000,0.300000
B2,0.250000,-0.700000
C3,1.400000,0.800000
```

没有先假定某个普通参数字段存储坐标。批量输入保留 ZIP 内其他 `.varN` 成员，
只按这个经过实际编辑器导入和保存确认的格式构造 `.var2`。
每份原生保存 DES 的 `.var2` 都再次读取核对，包括行顺序、ID 和坐标。

源 CSV 与 GUI 保存 DES 位于本地：

```text
flotherm_pack_data/validation/csv_ball_map_2026-10-25/ui/sample.csv
flotherm_pack_data/validation/csv_ball_map_2026-10-25/ui/ui-seed.des
```

正式批量数据位于：

```text
flotherm_pack_data/validation/csv_ball_map_2026-10-25/formal/
  baselines/<family>.des, <family>.xml, replay.xml, run.json
  <family>/inputs/<case>.des
  <family>/native/<case>.des, <case>.xml, replay.xml, run.json
  <family>/definitions.json
  nonempty-map.csv
```

所有判断来自真实导出的 FloXML、原生保存 DES 和 CSV 源数据；
未用项目生产几何生成器或 DLL 计算探针判断导入布局规则。

## 坐标、单位、ID 与单球几何

三个球的原生输出名称为 A1、B2、C3，中心坐标（mm）分别为：

```text
A1 = (-1.1,  0.3)
B2 = (0.25, -0.7)
C3 = (1.4,   0.8)
```

- CSV 的 X、Y 是相对于封装原点的实际坐标，不是网格行列索引。
- 从编辑器以 mm 导入后，FloXML 以 m 保存；报告统一乘 1000 比较。
- 不交换轴、不翻转 Y、不将坐标吸附到 e 网格，也不按质心或包络重新居中。
- 单球非零坐标 (0.7,-0.2) 保持不变，证实没有单球自动居中。
- 将所有坐标平移 (+0.35,-0.4)，输出也逐球平移相同数值。
- 颠倒 CSV 行顺序，不改变 ID 对应的球位集合。
- 两个不同 ID 使用相同坐标时，输出两个重合对象，不按位置去重。

离散输出仍使用统一球直径 b 和球层高度 A1：

```text
size_x = size_y = b*sqrt(pi)/2
size_z = A1
z_bottom = 0
```

改变 b=0.5→0.4 只改变横截面，改变 A1=0.4→0.5 只改变高度，导入中心坐标不变。

## 与其他阵列参数的组合

以下每类封装均执行同一组探针，三球 CSV 为默认输入：

| 探针 | 输出主球数 | 输出中央球数 | 结果 |
| --- | ---: | ---: | --- |
| csv3 | 3 | 0 | 按文件直接生成 |
| csv3_grid_counts，MD=3、ME=7 | 3 | 0 | 不重新网格化或按行列裁剪 |
| csv3_pitch，e=1.1 | 3 | 0 | 不按 e 缩放导入坐标 |
| csv3_diameter | 3 | 0 | 仅球截面尺寸改变 |
| csv3_height | 3 | 0 | 仅球高度改变 |
| csv3_stagger | 3 | 0 | 主阵列交错不筛选 CSV |
| csv3_depop | 3 | 0 | 中央去球不筛选 CSV |
| csv3_explicit，网格名单仅保留一个球位 | 3 | 0 | CSV 优先于网格保留名单 |
| csv3_center，开启中央 2×2 | 3 | 0 | 不额外生成中央四球 |
| csv3_center_stagger | 3 | 0 | 中央阵列及其交错不生效 |
| csv3_all_filters | 3 | 0 | 同时开启上述选项仍由 CSV 唯一决定 |
| csv1_offset | 1 | 0 | 非零单球坐标保持 |
| csv3_reordered | 3 | 0 | 行重排不改变球位集合 |
| csv3_translated | 3 | 0 | 按输入坐标整体平移 |
| csv2_same_position | 2 | 0 | 两个 ID、一个不同中心位置 |
| csv_empty | 0 | 0 | 开启空图产生零球 |
| csv_disabled | 25 | 0 | 关闭开关，忽略已有三球载荷，恢复 5×5 |
| csv_disabled_explicit | 1 | 0 | 关闭开关，使用显式网格名单 |

本次未从“仅有 On 开关”推测 CSV 内容。输入与保存后的坐标载荷均确实存在。

## 对整体生成次序的修正

```text
if Solder Ball Map 开启:
    焊球输出 = CSV 坐标列表
    不另行生成 Central Balls
else:
    主阵列 = 非空显式网格保留名单
           或 [完整网格 ∩ 中央去球外围条件 ∩ 主阵列交错条件]
    中央阵列 = 独立中央网格 ∩ 中央阵列自己的交错条件
    焊球输出 = 主阵列对象 + 中央阵列对象
```

因此 CSV 模式的优先级高于此前总结的整个规则网格/中央加球路径。

## 复现与限制

捕获工具依据已确认的原生存储格式构造输入，再通过隔离配置、隐藏原生进程导出。
没有改写全局材料、安装预设或生产实现。

```powershell
uv run --locked --no-sync --cache-dir tmp/uv-cache python -m tools.csv_solder_ball_probes --installation 'E:/Program Files/Siemens/SimcenterFlotherm/2504' --output 'flotherm_pack_data/validation/csv_ball_map_recheck'
uv run --locked --no-sync --cache-dir tmp/uv-cache python -m tools.verify_csv_solder_ball_floxml --archive 'flotherm_pack_data/validation/csv_ball_map_recheck' --output 'tmp/csv_ball_map_recheck.json'
```

只核验已保存的正式数据，不启动 PACK：

```powershell
uv run --locked --no-sync --cache-dir tmp/uv-cache python -m tools.verify_csv_solder_ball_floxml
uv run --locked --no-sync --cache-dir tmp/uv-cache ruff check tools/csv_solder_ball_probes.py tools/verify_csv_solder_ball_floxml.py
```

验证器还要求保留上述 ui-seed.des，核对其真实导入内容与批量输入一致。
本结论覆盖有效的非空任意坐标、空图、坐标重复和所列组合；
未穷举重复 ID、异常 CSV、单位切换、越界位置和等效材料表示。
原始数据按仓库规则只保存本地，Git 保存工具、研究说明和机器可读验证结果。
