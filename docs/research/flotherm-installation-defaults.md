# FloTHERM 2504 安装目录文本默认值调研

> 2026-10-11 更新：本文记录早期调研。原生默认值已接入运行时；旧快照和脚本已删除，
> 当前命令与范围见 [默认参数库](../../default_parameters/README.md)，历史文件通过 Git 查看。

调研日期：2026-09-30。目标是找到可复核的封装默认值与输出契约，作为开发期证据。
生产代码继续手写模板，不依赖用户的 FloTHERM 安装或许可证。

## 结论与来源

用户提供的 PID 11212 对应：

```text
E:/Program Files/Siemens/SimcenterFlotherm/2504/WinXP/bin/flopack.exe
```

同一安装根目录下，`flocentral/flopack/<家族>/*.des` 是可直接读取的 UTF-8 文本，
每行 `字段|值`。共找到 342 份预设，并保存字段、来源相对路径和原文件 SHA-256 到
[调研快照](../../flotherm_pack_data/installation/presets.json)。

| 安装子目录 | PackStudio 家族 | .des 数量 |
| --- | --- | ---: |
| `cbga_fc` | Flip Chip CBGA | 49 |
| `pbga_fc` | Flip Chip PBGA | 45 |
| `pbga_wb` | Wirebond PBGA | 36 |
| `chip_array` | FBGA/FSBGA | 38 |
| `QFN` | QFN | 46 |
| `pqfp` | QFP | 61 |
| `tsop_conv` | SOIC/SOP/TSOP/TSSOP | 67 |

当前 25 个生产尺寸预设中，21 个非 Bare Die 预设都有同名安装记录。
逐项对比 `die.length → Ld`、`die.width → Wd`，42 个数值全部一致。
这是芯片 X/Y 默认值的复核结果，不代表其余所有字段或建模分支已经核验。
4 个 Bare Die 预设没有对应 `.des`；不能把目录中不存在记录当作零值或缺省规则。

## 实例与解释范围

`cbga_fc/CBGAFC_49_6X6mm.des` 包含：

| 字段 | 安装值 | 当前可核对的意义 |
| --- | --- | --- |
| `D` / `E` | 6 / 6 | 封装 X/Y 尺寸，mm |
| `Ld` / `Wd` | 1.8 / 1.8 | 芯片 X/Y，mm |
| `td` | 0.61 | 芯片厚度，mm |
| `MD` / `ME` | 7 / 7 | 焊球阵列两向数量 |
| `e` / `b` / `A1` | 0.8 / 0.5 / 0.4 | 焊球间距、直径、层高度，mm |
| `tC4` / `bC4` / `MNC4` | 0.1 / 0.12 / 49 | 凸点厚度、直径、总数 |
| `k_substr` | Alumina (Typical) | 材料名称引用，不是导热率数值 |
| `P`、`NVx`、`kx_substr` 等 | 空串 | 尚未在此文件中给定，不能解释为 0 |
| `radio_BGA_modeling` | 4 | 原程序枚举编码，需 UI/FloXML 证据解码 |

该文件自身 `designDate=20020705`，`rev=2.3.1`；安装版本为 2504 并不意味着每份记录
都在 2504 更新。各记录可能还包含局部网格、多层铜覆盖、材料或顶盖分支等旧字段。
不应把整个字段集合直接映射为可编辑的生产参数。

## 已打开的 PACK 界面核对

通过 computer-use 检查 PID 对应窗口：初始没有打开封装，Save 不可用。
New 向导提供当前项目覆盖的八类家族，包括 Bare Die。
选择 Flip Chip CBGA 后，Customize Template 页显示：

- Outline Type：Standard Outline；
- JEDEC Footprint：CBGAFC_49_6X6mm；
- Top Cover：Bare Die。

这些值与当前生产基准相符。检查后取消向导，未创建或保存参考封装。
这也说明 Bare Die 的 UI 入口存在，而 `.des` 文本目录没有相应家族文件夹；
此目录不是完整 UI 默认值数据库。

## 材料与其他默认配置

`flocentral/flopack/Library/Material.mat` 至 `Material3.mat` 只有
`cndt_type`、`gp_name`、`mat_name` 三类标识，没有密度、比热、导热率数值。
抽样的 `flocentral/Libraries/FloTHERM_Libraries/Materials` 条目以
`#FFFB V3.6 FLOTHERM 4.1` 开头，后续是二进制序列，不适合按文本提取热物性。
材料完整物性仍应使用已捕获的 FloXML / UI 材料证据。

`examples/FloXML/FloXML Files/Project FloXML Examples/Default.xml` 是可读的工程级
默认示例，例如 flow_heat、辐射关闭、重力 9.81、环境温度 308.15 K、参考压力 101325 Pa。
这些是工程/求解设置，不是封装 `.des` 的模板默认值，不替换 PackStudio 的环境预设。
`flocentral/Templates/Defaults/*.project` 与用户 config 文件也需要与标准封装尺寸资料区分。

## ECXML 契约

`WinXP/PlugIns/ECXML_PLUGIN_SCHEMA/ECXML.xsd` 给出了本机可用的 ECXML 1.0 契约。
已原样存入 [ECXML 输出目录](../../output_format/ecxml/README.md)，作为无需安装 FloTHERM
即可执行的测试输入。附件中的 XML 示例为图片，渲染核对 Block (Box) 的 location、size、
material、powerDissipation 结构，并结合 XSD 补齐根节点、材料及 assembly 定义。

[Siemens 格式介绍](https://blogs.sw.siemens.com/simcenter/ecxml-jedec-jep181-thermal/)
说明 ECXML 用于跨电子热仿真工具的模型交换；这不意味着它具备 PTA 的边界与网格语义。
本次导出严格采用安装 XSD 的块模型子集，限制与映射详见输出目录 README。

## 可复现命令与后续使用

```powershell
uv run --locked python tools/research_flotherm_installation.py `
  'E:\Program Files\Siemens\SimcenterFlotherm\2504' `
  --output flotherm_pack_data/installation/presets.json
```

脚本只读安装目录，严格校验 `.des` 行和重复字段，保留空值并输出哈希。
快照和脚本仅开发期使用。后续扩展尺寸库可优先选取这里的独立结构参数，逐项核对
材料、层厚、阵列/引脚和条件分支，再以 JSON 生产预设纳入回归；本次不扩大生产预设数量。

## TASK16 后续落地（2026-09-30）

完整 342 条已无损转录到 default_parameters/flotherm/，字段和物性默认值迁入模板/材料 JSON。
21 个源预设的 Ld/Wd 运行时直接读取转录库；当前保持 25 个已验证生产选项。
342 条均含 Ld/Wd；尚未全部开放的原因是其余结构字段、枚举、材料及派生规则未完成适配验证，
不能笼统解释为“资料不完整”。详见 [参数库契约](../../default_parameters/README.md)。
