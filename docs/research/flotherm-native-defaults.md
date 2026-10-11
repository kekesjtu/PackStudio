# PACK 2504 原生默认值逆向提取

## 结论

可以绕开 FloSCRIPT/FloXML，直接批量取得 PACK 原生初始化后的参数。
本次分析的是本机安装的 C++ DLL 二进制，没有得到 Siemens 的源码。
已经保存 342 个 `.des` 预设的默认向导分支，以及 74 个预设的 4-Layer 分支。
这些快照明显比单独读取 `.des` 完整，但还不能称为全功能、全选项组合的完备默认值库。

当前生产适配确实存在缺值继承不准确的问题。仅对 36 个 Wirebond PBGA 预设的
基板厚度、键合线总数、过孔间距三个字段比较，就发现 56 处差异。
此前“342 个预设均可生成和导出”的验收证明结构可用，不能证明所有默认值与 PACK 相同。
本次保存提取工具与证据，没有把未经完整适配核对的快照直接接入生产参数库。

## 文件与来源

| 文件 | 内容 |
| --- | --- |
| `flotherm_pack_data/installation/native_defaults.json` | 342 个原生默认分支快照 |
| `flotherm_pack_data/installation/native_defaults_4layer.json` | Chip Array 38 个、Wirebond PBGA 36 个四层分支 |
| `flotherm_pack_data/installation/native_defaults_audit.json` | 来源、规则、归档 FloXML 核对及生产差异清单 |
| `tools/extract_pack_native_defaults.py` | 原生参数批量提取入口 |
| `tools/pack_native.py` | 对指定 DLL 构建的原生对象访问 |
| `tools/inspect_pack_binary.py` | 不加载 DLL 的 PE 导出符号与反汇编检查 |
| `tools/audit_pack_native_defaults.py` | 可重复执行的交叉审计 |

安装根目录为 `E:\Program Files\Siemens\SimcenterFlotherm\2504`。
原始文本仍在 `flocentral/flopack/<family>/*.des`，逐文件路径与原始字节哈希保存在快照中。
安装目录的文件没有被修改；DLL 本身没有复制进仓库。

原生读取严格匹配以下四个文件的 SHA-256，拒绝加载其他构建。

| DLL | SHA-256 |
| --- | --- |
| `flopackdatasets.dll` | `43312861dc31e9936bb407104292ce42ef7690a7183f44cd10b969fc8679b4a9` |
| `flopackdes.dll` | `2ad00011d2399629ea076f350f643973117e452eab8f2d313b64dbb9b49e961e` |
| `flopackpackages.dll` | `f0a6363dad8e2be5020d9e8704ec427ef9c669218889e202a7228650b883123c` |
| `flopackproperties.dll` | `b1e37b8db2d2de4fe4fec8781c9051a2b4704827743d5132f08729d3f1acf38a` |

## 为什么 `.des` 不全，怎样补齐

DLL 保留了大量 C++ 导出符号，包括向导的 `initialise`、预设加载器
`DesPackageTranslator::loadDESPackage`、封装的 `setWizardData`、数据集工厂和参数序列化函数。
缺失值不是简单集中在另一张完整文本表里：有些是构造默认值，有些在向导初始化时设置，
还有些依据封装尺寸、阵列和选项计算。

反汇编 `FlopackBackendCtrl::createPackage`（`flopackbackend.dll`，RVA `0x27a0`）可见，
正常创建过程在加载 `.des` 后调用封装的 `setWizardData`，再进行模型实现。
本次在独立 Python 进程中复用参数阶段的调用链：

```text
loadDESPackage(source.des)
  → 构造对应家族的 WizardPackageDataSet
  → initialise()
  → 设置已选的向导分支（可选 4-Layer）
  → package.setWizardData(wizard)
  → createPackageDataSet / package.getData
  → 原生 desStringFromProperty 序列化有值参数
```

没有执行几何实现或导出。这保留了 PACK 本身的初始化和派生过程，避免在我们的工具中
用同名字段或文件名猜默认数值。原生对象在读取后调用对应析构函数释放。

4-Layer 通过 `FlopackEnumValue::valueFromDesString` 设置，并检查内部枚举值确为 1。
DES 枚举有编号起点，不能把显示编号直接当作内部索引。四层分支还验证了过孔由 5×5
改为 3×3、金属表中有值层由两层改为四层，确保分支实际生效。

## 已确认的规则

Wirebond PBGA 的 `setLayerData` 位于 `flopackpackages.dll` RVA `0x40810`。
反汇编中的浮点常量以米计；转换为毫米后得到：

| 向导分支/条件 | 基板厚度 |
| --- | --- |
| 2-Layer，D ≤ 23 mm 且 E ≤ 30 mm | 0.36 mm |
| 2-Layer，其余尺寸 | 0.56 mm |
| 4-Layer | 0.56 mm |

D 与 E 分别对应原生长度和宽度，不能擅自互换以套用判定。
RVA `0x408df`、`0x40924` 分别读取 `0.023`、`0.030` 阈值；
RVA `0x50c50` 的厚度选择表为 `0.00056`、`0.00036`。

Wirebond PBGA 的 `setThermalViaData`（RVA `0x40990`）给出：
2-Layer 使用 5×5 过孔，4-Layer 使用 3×3；过孔间距取该预设的焊球间距。
因此不能对全部预设继承固定 1.27 mm。

`setDieTypeData`（RVA `0x40660`）在 actualDie 分支根据实际阵列和去球区计算键合线数，
不能用预设文件名里的数量替代。有中央去球区时，还会联动背面铺铜/扩散结构相关参数。

Chip Array 的 `setLayerData`（RVA `0xab20`）在两层/四层分支分别设置
0.36/0.56 mm。金属层表还包含厚度、覆盖率，以及 Wirebond PBGA 的过孔断开标记。
表格读取值为 SI 单位；序列化属性的单位由同组 `lengthUnit` 等字段记录。

几个直接提取的例子：

| 预设/分支 | 基板厚度 | 键合线数 | 过孔阵列 | 过孔间距 |
| --- | --- | --- | --- | --- |
| WB `PBGA_121_15X15mm`，2-Layer | 0.36 mm | 121 | 5×5 | 1.27 mm |
| WB `PBGA_121_15X15mm`，4-Layer | 0.56 mm | 121 | 3×3 | 1.27 mm |
| WB `PBGA_352_35X35mm`，2-Layer | 0.56 mm | 352 | 5×5 | 1.27 mm |
| WB `PBGA_208_17X17mm`，2-Layer | 0.36 mm | 192 | 5×5 | 1.00 mm |
| FC `PBGAFC_49_6X6mm`，默认分支 | 1.15 mm | — | — | — |

这也解释了此前 0.56 与 1.15 mm 的疑问：上述 Wirebond 与 Flip Chip 预设确实不同。
但这不代表现有项目所有其他预设的继承值正确。

## 验证结果与生产差异

- 默认分支家族计数：Chip Array 38、CBGA FC 49、PBGA FC 45、PQFP 61、QFN 46、SOP/TSOP 67、PBGA WB 36。
- 342 项源文件哈希与既有无损转录一致，1026 项 `Ld/Wd/td` 与原生读取一致。
- 512 项条件规则断言通过，包括基板厚度、过孔数、间距和金属层数。
- 六份既有 FloXML 的基板厚度通过交叉检查；没有新运行 FloSCRIPT。
- 两次独立进程全量提取的 JSON 字节完全一致，SHA-256 为
  `31633d2f8e7616da84a39bb731b30a87a2fe886c4d4d40cf665d1e7c3f45817d`（UTF-8/LF）。
- 342 默认分支含 19,874 个有值属性实例、4,315 个未赋值实例。
  `native_state=0` 保留为 `null`；不能序列化未初始化存储后把随机数当默认值。
  原生状态 4 的 94 个属性实例有实际值，不能与未赋值混淆。

对生产参数的比较只覆盖 WB 的三个字段：厚度 22 处、键合线数 18 处、过孔间距 16 处，
共 56 处差异。例如 `PBGA_225_27X27mm` 的生产厚度为 0.36，原生值为 0.56；
`PBGA_169_23X23mm` 的生产过孔间距为 1.27，原生值为 1.5；
`PBGA_208_17X17mm` 的生产键合线数为 208，原生值为 192。
这不是全部家族、全部参数的差异总数。修正生产库时需要按项目保留的分支逐字段映射，
并处理金属层、背面结构和材料联动，不能只统一替换一个厚度常量。

## 完备性的边界

本次覆盖七个有 `.des` 预设的家族；Bare Die 不在这 342 个源预设中。
默认向导分支与两类四层分支均已提取；其他顶盖、slug、thermalDie 等分支尚未系统遍历。
复杂对话框、球位图、去球编辑器及非均匀热源的嵌套数据，不能仅凭属性字符串判定已完整恢复。
材料属性这里只得到名称引用，没有提取材料库的密度、比热、导热张量。
金属表里未指定的深度仍为空，后续几何实现可能自动定位，不应自行填零。

因此，这个入口已经解决“为数百个预设逐个导出 FloXML 来补默认值”的主要成本，
但还没有证明完整 UI 行为、几何和全部物性均与 PACK 一致。
它依赖本机指定 DLL 构建和 64 位 Windows，只作为研究工具；生产运行仍读独立 JSON，
不加载 Siemens DLL。生产适配的下一步应以这些原生证据替换已确认不准确的继承规则。

## 重现

```powershell
uv sync --locked --python-preference only-managed
uv run --locked python -m tools.extract_pack_native_defaults `
  'E:\Program Files\Siemens\SimcenterFlotherm\2504' `
  --output flotherm_pack_data/installation/native_defaults.json
uv run --locked python -m tools.extract_pack_native_defaults `
  'E:\Program Files\Siemens\SimcenterFlotherm\2504' --four-layer `
  --output flotherm_pack_data/installation/native_defaults_4layer.json
uv run --locked python -m tools.audit_pack_native_defaults

uv run --locked python -m tools.inspect_pack_binary `
  'E:\Program Files\Siemens\SimcenterFlotherm\2504\WinXP\bin\flopackpackages.dll' `
  --symbol '?setLayerData@WirebondPBGAPackage@'

$env:PACK_NATIVE_INSTALLATION = 'E:\Program Files\Siemens\SimcenterFlotherm\2504'
uv run --locked pytest tests/backend/test_pack_native_probe.py
```

提取命令可加 `--preset PBGA_352_35X35mm` 限定单个原始预设名。
未设置测试环境变量时，原生集成测试跳过；归档证据核对不依赖安装目录。
