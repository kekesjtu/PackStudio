# Chip Array 焊球操作对 Via 的原生影响

## 结论

PACK 原生 Chip Array 的 Via 不是根据“最终输出的所有焊球”逐个生成。
更准确的规则是：Via 使用规则主阵列的保留名单；中央加球不增加 Via，
CSV 任意坐标球位图也不直接替代 Via 的规则网格。

本次每种配置 31 组方案，覆盖 2-Layer／4-Layer × Accurate／Approximate，
共 124 份首次原生导出及 124 份 DES 原生重载导出。248 份正式 FloXML 全部核验通过。
8 个原生批次退出码均为 0，日志没有 ERROR；请求模式和其他输入均保留，
本次记录的保存重载数值差异为 0。

软件为 PACK 2504，文件版本 2025.13.1.1142；
Footprint 为 ChipArray_24_4X4mm_0_8，未填孔。
基础网格 5×5、球径 0.46、间距 0.8、离板高度 0.4 mm。

## 数量对照

下面结果在四种配置中一致。球数按导出的对象计数，主球与中央球分开记录。

| 操作 | 主球 | 中央球 | Via |
| --- | ---: | ---: | ---: |
| 完整 5×5 | 25 | 0 | 25 |
| 规则网格改成 4×6 | 24 | 0 | 24 |
| 主阵列交错，5×5 | 13 | 0 | 13 |
| 主阵列交错，4×6 | 12 | 0 | 12 |
| 中央去球，MDp=MEp=1 | 0 | 0 | 0 |
| 中央去球，MDp=MEp=2 | 16 | 0 | 16 |
| 中央去球，MDp=MEp=3 | 16 | 0 | 16 |
| 中央去球，MDp=1、MEp=2 | 10 | 0 | 10 |
| 中央去球，MDp=5、MEp=2 | 25 | 0 | 25 |
| 中央去球 2/2＋主交错 | 8 | 0 | 8 |
| 显式删除一个角球 | 24 | 0 | 24 |
| 显式仅保留一个球位 | 1 | 0 | 1 |
| 显式保留 24 球＋主交错 | 24 | 0 | 24 |
| 显式保留 24 球＋中央去球 | 24 | 0 | 24 |
| 显式外围 16 球＋中央 3×3 | 16 | 9 | 16 |
| 完整阵列＋中央 2×2 | 25 | 4 | 25 |
| 完整阵列＋中央 3×3 | 25 | 9 | 25 |
| 完整阵列＋中央交错 3×3 | 25 | 5 | 25 |
| 中央去球 2/2＋中央 3×3 | 16 | 9 | 16 |
| CSV 任意坐标 3 球 | 3 | 0 | 25 |
| CSV 3 球＋主交错 | 3 | 0 | 13 |
| CSV 3 球＋中央去球 2/2 | 3 | 0 | 16 |
| CSV 3 球＋显式仅保留一格 | 3 | 0 | 1 |
| CSV 3 球＋显式一格＋去球＋交错＋中央球 | 3 | 0 | 1 |
| 空 CSV 开关开启 | 0 | 0 | 25 |
| 关闭 CSV，保留其载荷 | 25 | 0 | 25 |
| CSV 两个 ID 位于同一坐标 | 2 | 0 | 25 |
| 平移 CSV 中全部坐标 | 3 | 0 | 25 |

此外球径、间距和离板高度各有一个独立变参对照。

## 规则主阵列怎样筛选

Via 与普通主焊球采用相同的网格保留结果：

1. 非空显式名单直接决定保留格；不再叠加中央去球和主交错。
2. 没有显式名单时，先按中央去球参数保留外圈，再应用棋盘格交错。
3. 主网格保留结果决定 Via；中央加球另建球阵列，不参与 Via 生成。

名单在 DES 中是保留格，不是删除格。DES 的 Y 行号从上向下，
转换为几何坐标时需反向；本次同时核对孔名称、实际坐标和球位，
没有仅凭对象数量推断对应关系。

中央去球的奇偶取整和边界退化也传递到 Via：
2/2 和 3/3 都留下 16 个；一方向达到总行列数的 5/2 对照恢复 25 个。
中央加球不会恢复这些已删除的孔，即使最终焊球数量又回到 25。

## CSV 为什么是例外

启用 CSV 时，最终焊球使用 CSV 的 ID、X、Y，中央加球及规则筛选不再影响这些 CSV 球。
但 Via 仍按 MD、ME、e 和显式名单／中央去球／交错来生成。

因此这时存在两条路径：

- 焊球：CSV 载荷 → 实际球位。
- Via：规则主网格 → 保留名单筛选 → Accurate 偏移或 Approximate 对齐。

例如 CSV 始终输出同样 3 个球，改变隐藏的主网格筛选后，
Via 可以是 25、13、16 或 1 个。平移 CSV 坐标并不会平移 Via。
空 CSV 也不删除 Via。

所以“Approximate 对齐焊球”应限定为规则网格的对应球位；
不能理解成它会追踪任意 CSV 坐标并与最终输出的每个球自动对齐。

## 剩余孔的几何与物性

删除孔不会让剩余孔重新居中、收缩间距或改变单孔材料。
中央加球也不改变原有 Via 的位置或物性。

对保留的网格位置，Accurate 仍使用原 Via Offset，本组为 0.4/0.4 mm；
Approximate 仍对齐规则球网格，不使用该偏移。
去球、交错、中央加球和 CSV 操作都不改变这条规则。

额外的焊球尺寸／布局变参：

| 参数变化 | Accurate Via | Approximate Via |
| --- | --- | --- |
| 球径 0.46→0.40 mm | 截面及物性不变 | 方柱边长 0.407664386→0.354490770 mm；k 从 32.005705340→42.263045312 W/(m·K)，密度／比热也重算 |
| 间距 0.8→0.65 mm | 孔网格间距跟随，仍叠加偏移 | 孔网格间距跟随，仍与规则球位对齐 |
| 离板高度 0.4→0.5 mm | 孔整体上移 0.1 mm，孔高和材料不变 | 同左 |

未填孔、球径 0.46 mm 的基准材料：

| 模式 | k，W/(m·K) | rho，kg/m³ | cp，J/(kg·K) |
| --- | ---: | ---: | ---: |
| Accurate | 168.45218125 | 3907.5282875 | 385.103990245 |
| Approximate | 32.005705340 | 2279.4949504 | 747.344578099 |

对去球类操作，上述材料逐孔保持不变；总孔体积和总导热通道数量随保留孔数减少。
全去除案例没有剩余孔，不以未使用的材料属性证明存在通孔。

## 证据与复现

正式原始数据仅存本地：
flotherm_pack_data/validation/chip_array_solder_via_2026-10-25/。
每个 profile 包含 inputs/、definitions.json、native/ 和 reload/。
所有输入键、非空 CSV 载荷、孔与球坐标、尺寸、高度、材料、模式和指纹均已回读。
机器可读摘要见 [results.json](../validation/chip-array-solder-via/results.json)。

已采集数据直接核验：

~~~powershell
uv run --locked python -m tools.verify_chip_array_solder_vias
~~~

重新采集需用不存在的新目录，使用隔离配置与 PowerShell 7 隐藏启动：

~~~powershell
$packInstallation = 'E:\Program Files\Siemens\SimcenterFlotherm\2504'
$viaOutput = 'flotherm_pack_data/validation/chip_array_solder_via-new-run'
$viaProfiles = @('l2_accurate','l2_approximate','l4_accurate','l4_approximate')
uv run --locked python -m tools.chip_array_solder_via_probes --prepare native --installation $packInstallation --output $viaOutput
foreach ($viaProfile in $viaProfiles) {
    & ./tools/replay_wb_via_stack.ps1 -Installation $packInstallation -Directory "$viaOutput/$viaProfile/native"
}
uv run --locked python -m tools.chip_array_solder_via_probes --prepare reload --installation $packInstallation --output $viaOutput
foreach ($viaProfile in $viaProfiles) {
    & ./tools/replay_wb_via_stack.ps1 -Installation $packInstallation -Directory "$viaOutput/$viaProfile/reload"
}
uv run --locked python -m tools.verify_chip_array_solder_vias --output $viaOutput
~~~

## 范围

结论限于上述 PACK 版本、Footprint、未填孔分支和输入组合。
本轮没有测试其他封装、用户临时材料、异常球位数据或任意去球边界。
未运行下游导入、网格及温度场求解，数量对应不代表热学精度验证。
