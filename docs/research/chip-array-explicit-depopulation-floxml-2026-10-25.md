# Chip Array 显式去球与中央去球叠加：新增 FloXML 验证

日期：2026-10-25。

## 结论

在本次验证的 PACK 2504 Chip Array / actualDie / standardOutline 分支中，
N 不是统一按“等效为块之前的实际剩余球数”计算。

当 Number of Bond Wires equals Solder Balls 为 Yes、csvBGA 为关闭时：

```text
depop_center = UNCHECKED: N = MD*ME
depop_center = CHECKED:  N = MD*ME - (MD-MDp)*(ME-MEp)
```

显式逐球保留名单不参与该 N 的计算，但会改变球的几何输出。
非空保留名单对几何的优先级高于自动中央去球，不会自动把两份删除集合取并集。
要得到删除并集，需在名单里明确列出扣除两份区域后的保留球位。
即使这样处理，N 也仍按上述参数计算，可能与名单长度不同。

本次仅记录 PACK 原生输出行为，没有修改 PackStudio 的实现或默认参数。

## 输入机制与证据范围

这次补充的是规则网格的显式逐球去球，不是任意坐标 CSV 球位图：

- DES `balls` 保存 `columnxrow:columnxrow:...` 形式的**保留**球位名单。
- 程序先定义需要删除的网格单元，再将其补集写入 `balls`。
- `csvBGA=UNCHECKED`；`central_balls=UNCHECKED`；`staggered_matrix=UNCHECKED`。
- `depop_center` 是中央去球开关，`MDp/MEp` 是中央去球参数。
- `balls` 为空表示没有显式名单，由阵列/中央去球参数生成几何；不表示删除全部球。
- DES 的 row 从上向下递增，与 FloXML 的物理 y 方向相反。逐球验证已做该坐标转换。

不要把 `balls`、`depop_center` 和 `csvBGA` 混为同一个机制。
此前空 CSV 球位图 N=0 的案例是另一条分支；本次没有非空任意坐标 CSV 的证据。

## 新增数据获取

原生软件为本机 `flopack.exe -f`，文件版本 `2025.13.1.1142`。
程序以隐藏窗口、独立配置、独立用户目录和独立材料目录运行。
没有修改安装预设、正在使用的 GUI 方案或全局材料库。

首先从已有 baseline/script.xml 的 new_package 命令创建全新基线并保存 DES/FloXML。
随后从该新基线生成 13 个输入 DES，通过原生 load_des、save_des、export_floxml 导出。
逐案例回读原生保存的 DES，确认每个修改字段与输入完全一致。

正式数据共 14 份新 FloXML：基线 1 份、探针 13 份。
之前的六个探索性导出未混入正式统计。

本地原始数据位置：

```text
flotherm_pack_data/templates/chip_array/validation/ball_count_2026-10-25/suite/
  baseline/fresh.xml, fresh.des, replay.xml, run.json
  inputs/<case>.des
  native/<case>.xml, <case>.des, replay.xml, run.json
  definitions.json
```

文件 SHA-256、软件指纹、输入回读、导出球位、物性反算与误差见
[逐例验证报告](../validation/chip_array_ball_count_floxml_2026-10-25.json)。
原始数据按 AGENTS.md 只保存本地；Git 中提交工具、汇总证据和研究说明。

## 设计与结果

所有案例的基线为 MD=ME=5，即 25 个候选球位。
中央去球启用时 MDp=MEp=2，自动中央区域为正中 3×3，共九个球位。
表中显式名单长度 0 表示没有名单，实际几何由其他参数生成。

| 案例 | 显式保留名单长度 | 中央去球 | 实际离散球数 | 物性反算 N |
| --- | ---: | --- | ---: | ---: |
| regular25 | 0 | 关 | 25 | 25 |
| remove_corner：删除一个角球 | 24 | 关 | 24 | 25 |
| remove_two_corners：删除两个角球 | 23 | 关 | 23 | 25 |
| remove_center_cell：删除正中一球 | 24 | 关 | 24 | 25 |
| explicit_perimeter：只保留外围 | 16 | 关 | 16 | 25 |
| central_only：自动中央去球 | 0 | 开 | 16 | 16 |
| central_plus_corner：名单仅删一个角球 | 24 | 开 | 24 | 16 |
| central_plus_center_cell：名单仅删正中一球 | 24 | 开 | 24 | 16 |
| central_plus_crossing：名单删一个角球和正中一球 | 23 | 开 | 23 | 16 |
| central_plus_precomputed_union：名单已扣除中央九球和一个角球 | 15 | 开 | 15 | 16 |
| central_plus_matching_list：名单恰好只保留外围 | 16 | 开 | 16 | 16 |
| central_plus_two_outer_corners：名单已扣除中央九球和两个角球 | 14 | 开 | 14 | 16 |
| independent_wire_count7：关闭自动线数，手工指定 Nw=7 | 24 | 关 | 24 | 7 |

### 排除“只是几何等效导致球块数量改变”

这些输出每个离散球对应一个 cuboid。
对非空名单，验证器把每个输出球的坐标映射回网格，并与输入保留名单逐位比较，全部一致。
因此 24、23、15、14 都是输入确定的实际保留球数，不是合并为等效块后的数量。
`central_plus_precomputed_union` 的 15 球与 N=16，直接否定了该解释。

### 排除“显式去球与中央去球自动取并集”

例如 `central_plus_corner`：

```text
显式删除集合：一个角球
中央删除集合：正中九球
若自动取并集：应剩 25-1-9=15 球
真实 FloXML：输出 24 球，逐位对应显式名单
```

中央去球参数仍参与 N 的计算，因此该案例反算 N=16，而不是 24 或 15。
`central_plus_center_cell` 和 `central_plus_crossing` 也排除了几何自动并集假设。

## 独立反算 N 与物性验证

先读取每个新 FloXML 的芯片长宽和水平键合线厚度。
再用已有材料库 Gold / Typical Epoxy，从两种键合线材料的三项物性分别反算 f：

```text
f_rho = (rho-1820)/17480
f_k   = (k_parallel-0.68)/295.32
f_cv  = (rho*cp-1605240)/942360
N     = f * 8*(Ld+Wd)/(pi*dw)
```

每例得到六个独立物性反算值：两种材料各三条路径。
反算 N 与输入参数候选规则的最大绝对误差为 `3.552713678800501e-14`。
没有先用输出球数作为 N 再去验证材料。

随后按候选 N 正向计算两种材料的 kx/ky/kz/rho/cp，
13 例共 130 个数值全部通过，最大相对误差为 `2.0215458955110583e-16`。
全部案例均保持八个键合线块及其两组材料引用，明确核对材料绑定。

判定依据只使用真正导出的 FloXML、其输入/保存 DES 和材料库。
原生 runner 只负责导出和保存软件指纹，没有用 DLL 数值调用或反汇编决定 N。

## 复现

再次导出必须给一个尚不存在的目录，避免覆盖证据：

```powershell
uv run --locked --no-sync --cache-dir tmp/uv-cache python -m tools.chip_array_ball_count_probes --installation 'E:/Program Files/Siemens/SimcenterFlotherm/2504' --output 'flotherm_pack_data/templates/chip_array/validation/ball_count_recheck'
uv run --locked --no-sync --cache-dir tmp/uv-cache python -m tools.verify_chip_array_ball_count_floxml --archive 'flotherm_pack_data/templates/chip_array/validation/ball_count_recheck' --output 'tmp/ball_count_recheck.json'
```

仅核验本次已保存的证据，不启动 PACK：

```powershell
uv run --locked --no-sync --cache-dir tmp/uv-cache python -m tools.verify_chip_array_ball_count_floxml
uv run --locked --no-sync --cache-dir tmp/uv-cache ruff check tools/chip_array_ball_count_probes.py tools/verify_chip_array_ball_count_floxml.py
```

本结论不扩展到任意坐标 CSV、其他封装、thermalDie 或所有交错阵列组合。
