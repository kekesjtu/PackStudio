# Wirebond PBGA 不等铜厚 Via 原生验证

## 结论

PACK 2504 的 Wirebond PBGA 离散 Via，在本次 2-Layer、4-Layer 对照中均符合：

$$
z_{\min}=A_1+t_{\rm top},\qquad
h_v=A_2-t_{\rm top}-t_{\rm bottom},\qquad
z_{\max}=A_1+A_2-t_{\rm bottom}
$$

不是“4-Layer 改成按底铜厚定位”。新增内部金属层也没有从 Via 柱高度中再次扣除：
所核对的四层方案各生成 9 根完整高度的 Via 柱，两层各生成 25 根。

## 原生采集和回读

- 软件：FloTHERM PACK 2504，文件版本 2025.13.1.1142。
- Footprint：PBGA_121_15X15mm，Actual Die，不含 Slug，默认离散 Via。
- 7 组四层方案：等厚基线、单独改变顶铜、单独改变底铜、正反不等铜厚、
  另一组等厚，以及同时改变基板厚度和离板高度。
- 2 组两层正反不等铜厚对照。
- 每组先原生保存 DES、导出 FloXML，再启动独立原生进程加载所存 DES、再次导出。
- 共 18 份正式 FloXML；回读 A1、A2、tz1、tz6、NVx、NVy 和离散模式值。
  核对内部层数、各 Via 高度、外铜层与 flag 的实际高度。
- 两次正式启动退出码均为 0，原生日志没有 ERROR。
- 保存重载仅有内部层深度等浮点末位差异，以 1e-11 容差核对通过。
  记录每份 XML、DES、回放脚本、启动器和原生程序的 SHA-256。

## 实测几何

长度单位均为 mm；所有四层方案孔阵列为 3×3，两层为 5×5。

| 层数 | A1 | A2 | 顶铜 | 底铜 | Via 底面 | Via 高度 | Via 顶面 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 0.6 | 0.56 | 0.018 | 0.018 | 0.618 | 0.524 | 1.142 |
| 4 | 0.6 | 0.56 | 0.010 | 0.018 | 0.610 | 0.532 | 1.142 |
| 4 | 0.6 | 0.56 | 0.018 | 0.040 | 0.618 | 0.502 | 1.120 |
| 4 | 0.6 | 0.56 | 0.010 | 0.040 | 0.610 | 0.510 | 1.120 |
| 4 | 0.6 | 0.56 | 0.040 | 0.010 | 0.640 | 0.510 | 1.150 |
| 4 | 0.6 | 0.56 | 0.025 | 0.025 | 0.625 | 0.510 | 1.135 |
| 4 | 0.8 | 0.70 | 0.012 | 0.030 | 0.812 | 0.658 | 1.470 |
| 2 | 0.6 | 0.36 | 0.010 | 0.040 | 0.610 | 0.310 | 0.920 |
| 2 | 0.6 | 0.36 | 0.040 | 0.010 | 0.640 | 0.310 | 0.950 |

这里的顶铜、底铜不是仅凭参数命名认定：输出中的 die_flag/toptrace 厚度与顶铜一致，
底面为 A1+A2-t_top；bottom_trace 厚度与底铜一致，底面为 A1。
因此不能用“顶底参数只是命名反了”解释这组输出。

## 怎样理解这个行为

如果几何目标是让 Via 正好接到两外层铜的内侧表面，其范围应为：

$$
[A_1+t_{\rm bottom},\quad A_1+A_2-t_{\rm top}]
$$

该范围的长度也是 A2-t_top-t_bottom。PACK 实际范围则为：

$$
[A_1+t_{\rm top},\quad A_1+A_2-t_{\rm bottom}]
$$

两者等长，实际范围相对前者整体平移：

$$
\Delta z=t_{\rm top}-t_{\rm bottom}
$$

因此：

- 顶底等厚：偏移为零，无法从默认模型看出这个问题。
- 顶铜薄、底铜厚：Via 整体向下偏，底端与底铜体积重叠，顶端与 flag 留隙。
- 顶铜厚、底铜薄：Via 整体向上偏，底端留隙，顶端与 flag 体积重叠。

例如四层顶铜 0.01、底铜 0.04：bottom_trace 为 0.60–0.64，flag 为 1.15–1.16，
Via 为 0.61–1.12。因此底端重叠 0.03，顶端留隙 0.03。
反向铜厚则出现底端留隙 0.03、顶端重叠 0.03。

这是几何生成位置的差异，不是单孔物性等效公式造成的。
其形式更像位置计算中顶底厚度的引用顺序不一致；这是依据输出的推断，
没有厂商源代码或设计说明，不能断定作者意图或正式归因。

“留隙”描述的是 Via 与铜层名义几何不接触，不意味着那里是真空或整个热路完全断开。
基板介质仍覆盖这段空间。它可能改变局部介质热阻；重叠处的材料占据和最终温度场，
还取决于下游导入、几何优先级及求解处理，本次没有验证。

## 原始数据与复现

正式数据仅保存在本地：
flotherm_pack_data/validation/wb_via_stack_2026-10-25-complete/。
其中 definitions.json 为方案定义，native/、reload/ 分别为两次实际原生输出，
results.json 为逐例计算结果。

可提交的机器可读报告：
[results.json](../validation/wb-via-stack/results.json)。

已完成采集的数据可直接离线核验：

~~~powershell
uv run --locked python -m tools.verify_wb_via_stack_floxml
~~~

重新采集时必须选择不存在的新目录。以下从仓库根目录运行，保持安装库不变：

~~~powershell
$packInstallation = 'E:\Program Files\Siemens\SimcenterFlotherm\2504'
$viaOutput = 'flotherm_pack_data/validation/wb_via_stack-new-run'
uv run --locked python -m tools.verify_wb_via_stack_floxml --prepare native --installation $packInstallation --output $viaOutput
& ./tools/replay_wb_via_stack.ps1 -Installation $packInstallation -Directory "$viaOutput/native"
uv run --locked python -m tools.verify_wb_via_stack_floxml --prepare reload --installation $packInstallation --output $viaOutput
& ./tools/replay_wb_via_stack.ps1 -Installation $packInstallation -Directory "$viaOutput/reload"
uv run --locked python -m tools.verify_wb_via_stack_floxml --output $viaOutput
~~~

本机正式运行使用 PowerShell 7、默认 RemoteSigned 策略和隐藏进程。
探索时的嵌套子进程启动异常、Windows PowerShell 5.1 未签名脚本拒绝、
以及不完整目录不计入本次 18 份正式输出；未修改系统执行策略。

## 范围

结论限定为该版本、该 Footprint、离散 Via 和本次铜厚／高度组合。
没有验证其他 Footprint、Isotropic/Orthotropic Via、去孔或任意内部层表编辑，
也没有验证下游求解器的重叠优先级与温度场。
