# Chip Array Via 与金属层原生验证

## 结论

PACK 2504 的 Chip Array，在本次 2-Layer、4-Layer 不等铜厚对照中均符合：

$$
z_{\min}=A_1+t_{\rm bottom},\qquad
h_v=A_2-t_{\rm top}-t_{\rm bottom},\qquad
z_{\max}=A_1+A_2-t_{\rm top}
$$

孔底、孔顶分别贴合底层金属上表面和顶层金属下表面，没有复现 WB 的整体偏移。
20 组通孔／铜厚方案、8 组金属表和布局补充方案，均由原生保存 DES 后重新加载导出，
共 56 份正式 FloXML。三个原生批次退出码均为 0，原生日志没有 ERROR。

## 范围和实测

软件文件版本 2025.13.1.1142；Footprint 为 ChipArray_24_4X4mm_0_8，Actual Die。
每种层数各验证等厚、顶铜单变、底铜单变、正反不等铜厚、第二组等厚、
同时改变 A1/A2、两个 Approximate 不等厚分支和一个 Filled Vias 分支。

以下取 A1=0.4 mm，长度单位为 mm：

| 层数 | A2 | 顶铜 | 底铜 | Via 底面 | Via 高度 | Via 顶面 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 0.36 | 0.010 | 0.040 | 0.440 | 0.310 | 0.750 |
| 2 | 0.36 | 0.040 | 0.010 | 0.410 | 0.310 | 0.720 |
| 4 | 0.56 | 0.010 | 0.040 | 0.440 | 0.510 | 0.950 |
| 4 | 0.56 | 0.040 | 0.010 | 0.410 | 0.510 | 0.920 |

其他起点／高度对照：A1=0.6、A2=0.7、顶铜=0.012、底铜=0.030，
两种层数均导出 Via 0.630–1.288，高 0.658。
Approximate 和 Filled Vias 对照保持相同纵向规则。

## 通孔几何和物性

- 完整规则阵列使用焊球 MD、ME、e；本次默认两种层数均为 25 个孔。
- Accurate：圆孔等面积方柱；中心为焊球规则网格加 vxoff/vyoff。
  额外的 0.2/0.1 mm 偏移与 4×6、0.7 mm 网格对照均符合。
- Accurate 未填孔：镀层金属与孔芯空气体积混合，导热率和密度体积加权，
  比热质量加权；三方向导热率相同。
- Accurate 填孔：本组变为纯铜，几何不变。
- Approximate：仍逐孔输出，截面扩大为焊球等面积方形，中心对齐焊球；
  原单孔材料按 (dv/b)^2 与 BT 再混合，本组原有 0.4 mm 偏移不再体现。
- 单孔材料及每个孔的坐标、尺寸、数量均独立重算，与原生输出比较。

## 金属层表

- Depth 从基板顶面量到该层顶面，底面为 A1+A2-Depth-Thickness。
- 两层表对应 tza1/tza2、coveragea1/coveragea2；四层对应 tz1..tz4、
  coverage1..coverage4，内部深度为 z2/z3。
- 完整层几何为 D×E×Thickness，Coverage 不缩小层面积。
- Trace 是金属与 BT 的各向同性混合材料，密度体积加权、比热质量加权。
  默认覆盖率依次为两层 20%/10%，四层 20%/90%/90%/10%。
- 对照修改顶层 50%、内部层 35%，材料符合各自覆盖率，整层几何不变。
- 四层显式 Depth=0.12/0.33 的内部层实际为 0.804–0.840、0.594–0.630。
- 仅改变内部厚度为 0.025/0.050 时，保留原 Depth 和层顶面，
  底面变为 0.766333333、0.590666667；Via 纵向范围不变。
- 默认向导初始化内部层采用 g=(A2-top-bottom-2*0.036)/3、
  Z2=top+g、Z3=top+2*g。该关系在默认 A2 的不同外铜厚初始化中通过核验；
  不把它当作已有表格每次都应重新均分的规则。
- Top Metal Layer Hole=1.4×1.0 mm：两种层数均保留完整 trace_0，
  另加同厚、居中的 Alloy-42 材料块 top trace hole；不是直接导出真空孔或四块边框。

## 证据与复现

正式原始数据：
flotherm_pack_data/validation/chip_array_stack_2026-10-25/。
native/ 为 20 组铜厚／通孔输出，metals/ 为 8 组补充输出，
reload/ 为这 28 份 DES 的原生重载。
definitions.json、metal-definitions.json 是输入定义，results.json 是完整核验结果。

可提交摘要及原生指纹见 [results.json](../validation/chip-array-stack/results.json)。
摘要不重复存储全部孔中心；完整位置列表在本地报告中。

已采集数据可直接离线核验：

~~~powershell
uv run --locked python -m tools.verify_chip_array_stack_floxml
~~~

重新采集必须使用不存在的新目录。从仓库根目录、PowerShell 7 运行：

~~~powershell
$packInstallation = 'E:\Program Files\Siemens\SimcenterFlotherm\2504'
$chipOutput = 'flotherm_pack_data/validation/chip_array_stack-new-run'
uv run --locked python -m tools.chip_array_stack_probes --prepare native --installation $packInstallation --output $chipOutput
& ./tools/replay_wb_via_stack.ps1 -Installation $packInstallation -Directory "$chipOutput/native"
uv run --locked python -m tools.chip_array_stack_probes --prepare metals --installation $packInstallation --output $chipOutput
& ./tools/replay_wb_via_stack.ps1 -Installation $packInstallation -Directory "$chipOutput/metals"
uv run --locked python -m tools.chip_array_stack_probes --prepare reload --installation $packInstallation --output $chipOutput
& ./tools/replay_wb_via_stack.ps1 -Installation $packInstallation -Directory "$chipOutput/reload"
uv run --locked python -m tools.verify_chip_array_stack_floxml --output $chipOutput
~~~

启动器复用上次 WB 验证工具，只负责隔离环境、隐藏运行、原生日志和指纹，
不包含 WB 的几何计算。未修改安装库、用户现有方案或生产模板。

## 笔记交付与限制

在用户指定的桌面笔记 packages/01_Chip_Array/ 下新增 Vias.md、Metal_Layers.md，
并为总览对应章节加入链接；这些文件在仓库外，不随 Git 提交分发。

本轮只验证上述 Footprint、模式与数值组合。未重测显式去球、中央去球、
交错阵列或任意坐标表，不外推所有几何边界与无效输入。
金属表补充变参通过原生 DES 加载，不代表穷举 UI 操作。
未验证导入器对重叠区域的材料优先级、网格与温度场。
