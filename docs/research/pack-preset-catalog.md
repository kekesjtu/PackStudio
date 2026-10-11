# PACK 预设与材料 JSON 库

## 结果与范围

`default_parameters/presets/<family>/<原预设名>.json` 保存七类全部 342 个安装预设，
一项预设对应一个文件。材料独立放在 `default_parameters/materials/<category>/*.json`，
共 10 类、131 项，预设通过完整材料名称引用，两个 `index.json` 保存索引与文件 SHA-256。

数据来自本机 PACK 2504 的 `.des`、原生初始化/向导计算，以及逆向确认的隐式参数。
没有运行 FloSCRIPT、没有新导出 FloXML，没有复制 Siemens DLL，也没有继承项目模板兜底数值。
原文件的全部键值及 SHA-256 都保存在每个预设的 `source` 中。

每个文件的 `branches.default` 包含实际芯片、标准外形和默认顶部结构的向导参数；
Chip Array 38 项与 Wirebond PBGA 36 项同时包含 `branches.four_layer`，共 416 个分支。
PQFP/SOP 的向导子类型按所选预设的 LQFP/MQFP/TQFP、SOP/SSOP/TSOP/TSSOP 设置，
避免把向导构造的 LQFP/SOP 初始选项误记到其他子类型。
顶盖内部的 encapsulant/lid/plate 子对象全部保留，包括尚未选中的已有参数。

这是原预设默认状态的参数库，不是 PACK 全部交互选项组合的枚举，也没有新增项目删去的功能。
thermalDie、非标准外形、用户自定义 slug 等改变向导行为后的状态，不是这批文件的默认分支。
切换这些状态不能直接复用默认分支的派生参数。本次先提供独立读取接口；
现有建模选择器仍使用既有 `source_adapters.json`，未在这次数据建库中修改几何适配。

## 文件契约

预设 schema 为 `packstudio.preset/v1`。主要结构如下：

```text
id / family / default_branch
source: path / sha256 / des_fields / binary_sha256
material_references: [完整材料名称, ...]
branches:
  default:
    wizard: {选项名: {value, choices?, comment}}
    groups:
      die:
        enabled / native_valid / native_type / comment
        properties: {原生属性名: {status, kind, value?, unit?, native?, comment}}
      metalLayers:
        properties / metal_layers
      topCover:
        properties / children: {encapsulant, lid, plate}
  four_layer: 同上（有此选项的预设）
```

`native.state=0` 表示原生属性未赋值。不能读取它的数值内存：那是未初始化存储。
JSON 不用裸 `null` 来掩盖这种情况，字段状态明确区分：

| status | 意义 |
| --- | --- |
| specified | 原生参数已赋值，保存类型化 value |
| calculated | 已展开隐式规则，保存结果并在 comment 写明算法 |
| fixed | 几何实现固定参数，例如 dieMaterial=Silicon (Pure) |
| not_applicable | 当前分支没有该结构/方向/槽位；没有虚构的数值 |
| user_input | PACK 没给额定温度、最大功率等器件限值；需用户输入 |
| not_specified | 可选分支没有指定材料名称 |
| action | UI 编辑按钮；真正的数据在 Dialog 属性中 |

空字符串可以是有效的备注、厂商、零长度文本，或源文件的无损记录。
运行参数从 `branches` 读取，不能重新从 `source.des_fields` 猜值。
新增未识别的未赋值数值会使提取失败，避免一律用“不适用”遮盖未知默认值。

## 隐式数据与计算

- 金属表：保留厚度、覆盖率、过孔断开标记、原生内层深度；顶层 depth=0，
  底层 depth=A2-thickness，z_from_substrate_bottom=A2-depth-thickness，单位米。
  四层内层沿用原生规则：gap=(A2-top-bottom-2*solid)/3，
  depth1=top+gap，depth2=top+2*gap。未定义的表行保留槽位并标记 not_applicable。
- WB 基板、过孔、线数与背面结构：直接保留原生 setWizardData 的计算结果，
  对应 JSON comment 写明尺寸阈值、焊球间距、去球矩形和四层扣除 2 mm 等规则。
- Chip Array 线数：逆向 `realise` RVA `0x3ff0/0x4040`，启用球位图时取列表长度，
  否则 MD*ME；中央去球开关启用时减 (MD-MDp)*(ME-MEp)。
- QFN 离散键合线步数：原生属性未赋值，但 getter（packages RVA `0x31080`）
  返回至少 1，文件保存实测返回值与规则，而不是猜一个模板默认值。
- QFP/SOP 自动 leadframe 覆盖率：默认枚举 noDefaultIsBe，保存 100*B/e 的百分数。
- 非均匀热源：保存原生模式、区域列表与功率矩阵；342 个预设均为空配置。
  如遇非空布局，当前提取工具会失败，要求先确认 ABI，不能丢弃数据后声称完整。
- 球位图与编辑器：保留名称、米制位置及原生坐标列表；坐标列表是保留球位，
  不应因 Depopulation 类名就当成删球名单，更不能自动改动开关。

`ChipArray_48_6X6mm_0_5` 的源列表有 48 个坐标，但原生默认去球开关关闭，
其原生“线数等于焊球数”计数函数返回 49；80 球源同理返回 81。
文件同时保存列表、开关和该计数，并说明算法，不用文件名强行纠正原生状态。
当前项目的显式列表适配仍采用 48/80；两者的行为差异需要在未来几何适配时单独核对。

Flip Chip 的默认等效基板仍为 1.15 mm；默认没有显式 core via/built-up 结构，
这些空字段不替换为 WB 的 5×5 过孔或 0.56 mm。Chip Array 的 lengthLml/widthWml
是金属开孔尺寸，原生未定义孔，不能拿整层尺寸补进去。

## 材料契约

材料 schema 为 `packstudio.material/v1`，包含完整名称、类别、密度、比热、发射率、
导热模型和 `native_storage`。原生 MaterialLibrary::populateBuiltInMaterials
只加载内建材料，未读写用户材料文件；构造期间的 FLOCENTRALDIR 修改会恢复。

常数各向同性材料保存标量 k，正交材料保存 kx/ky/kz，温度相关材料保存基准 k、
系数和参考温度。保留温度相关定义，没有按某个假定温度把它变成常数。
原生存储中非当前类型的字段不是有效物性：例如各向同性材料的三个零值 kx/ky/kz
不能表示物理导热为零，正交材料残留的标量与温度系数也不能混用。
温度系数按原生表示保存；本次没有新增求解器插值/温度评价实现。

Silicon (Pure) 还作为不可编辑的 dieMaterial 引用写入每个预设。
该名称在原生几何实现（realise RVA `0xc0e0/0xf700/0x28250/0x43210`）中固定创建，
不会出现在普通 die 数据集或 `.des` 字段中。

## 程序读取与分发

```python
from packstudio.preset_catalog import PresetCatalog
from packstudio.material_catalog import MaterialCatalog

catalog = PresetCatalog()
record = catalog.read("PBGAFC_49_6X6mm")
branch = catalog.read_branch("PBGA_121_15X15mm", "four_layer", resolve_materials=True)
copper = MaterialCatalog().read("Copper (Pure)")
```

这些接口只读项目 JSON，支持源码、wheel 和 PyInstaller 分发，不加载安装 DLL。
读取验证 schema、索引身份、文件字节哈希与材料名称；返回深拷贝避免调用者污染缓存。
文件编辑后应重建索引哈希并重启进程。wheel 的 data-files 覆盖全部分类目录，
源码与 EXE 继续使用已有递归分发配置。

## 重现与验证

```powershell
uv run --locked python -m tools.extract_pack_catalog `
  'E:\Program Files\Siemens\SimcenterFlotherm\2504'
uv run --locked pytest tests/backend/test_preset_catalog.py
$env:PACK_NATIVE_INSTALLATION = 'E:\Program Files\Siemens\SimcenterFlotherm\2504'
uv run --locked pytest tests/backend/test_pack_catalog_probe.py
```

提取工具在执行原生代码前核验七个 DLL 的指定 SHA-256，拒绝其他构建。
`--output tmp/pack-catalog-repeat` 可独立重提取并逐文件比较；输出 UTF-8/LF，没有时间戳。
单元测试检查 342/416/131 计数、全部来源与材料引用、完整属性状态、金属自动深度、
嵌套对象、枚举子类型、错误路径/哈希及缓存隔离。可选集成测试将现场原生值与 JSON 比较。
这些检查证明参数保存与读取正确；并不替代全部几何、全部材料温度行为或热仿真精度验证。
