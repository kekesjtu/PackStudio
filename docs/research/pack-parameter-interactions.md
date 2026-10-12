# PACK 2504 参数联动一致性审计

日期：2026-10-12。范围：当前 PackStudio，排除 requirements.md 和 ADR 中明确的功能取舍。

后续状态：两类前端转移缺陷已在 TASK21 修复，见
[修复验证](../validation/pack_frontend_fixes.json)。下文保留修复前审计事实与原始证据。
11项已开放参数的物性联动缺口已在 TASK22 修复，见
[PACK等效材料联动](pack-material-couplings.md)；该记录还说明 PQFP 数量取整及原13个候选的分类。

## 结论

**预设参数库一致，已开放参数的联动与模型效果尚不完全一致。**

- 本机 DLL 重新读取 342 个默认分支及 74 个四层分支，共 416 份快照，与独立 JSON 库全部一致。
- 八类模板共 212 个生产字段进入扫描；193 个字段重放原生 dataset setter，2 个顶盖字段重放
  向导选择，15 个字段仅做项目模型探针，2 个子类型字段沿 Footprint 联动路径检查。
- 14 个字段改变后不改变物理模型。剔除 Bare Die 翻转的监控点/面热源差异，以及 PACK 本来
  就没有默认输出效果的 SOP 键合线长度后，得到 **11 个有交叉证据的无效模型参数**；
  SOP 总长另列待确认，不把所有“无变化”都算缺陷。
- Flip Chip CBGA/PBGA 均复现两类前端缺陷：切换 Footprint 重置独立顶盖选择；切换顶盖后
  保留隐藏尺寸覆盖，导致生成失败。
- 29 个 Wirebond PBGA 原生默认分支启用 backsideSpreader；当前生成器没有相应结构。
  这是额外的结构一致性差距，不能通过默认数值一致或旧基准回归通过来消除。

本次提交只增加审计工具、证据和集成测试，没有修改生产默认值或生成逻辑。

## 证据与复现

安装：`E:\Program Files\Siemens\SimcenterFlotherm\2504`，64 位 Windows。
执行前核验四个参数 DLL 与三个扩展 DLL 的 SHA-256；原始 DES 逐项核验哈希。
没有修改安装文件、复制 DLL、运行 FloSCRIPT 或新导出 FloXML。

| 文件 | 内容 |
| --- | --- |
| `docs/validation/pack_interactions.json` | 416 份快照结果、212 字段探针、顶盖/材料/BGA/组合检查和历史交叉证据 |
| `docs/validation/pack_interaction_disassembly.json` | 有界反汇编、实现阶段 getter 引用与 DLL 哈希 |
| `docs/validation/pack_frontend_interactions.json` | 真实 schema 的四次 UI 转移及其后端验证结果 |
| `tools/pack_native_interactions.py` | 原生 wizard 与 dataset setter 重放，不进入生产运行路径 |
| `tests/backend/test_pack_interaction_probe.py` | setter 读回、状态重置、嵌套顶盖和源文件不变验证 |

```powershell
uv run --locked python -m tools.audit_pack_interactions 'E:\Program Files\Siemens\SimcenterFlotherm\2504'
uv run --locked python -m tools.inspect_pack_interactions 'E:\Program Files\Siemens\SimcenterFlotherm\2504'
uv run --locked python -m tools.audit_pack_frontend
$env:PACK_NATIVE_INSTALLATION = 'E:\Program Files\Siemens\SimcenterFlotherm\2504'
uv run --locked pytest tests/backend/test_pack_interaction_probe.py
```

前端工具临时复制研究 harness 到测试目录，使用 Python 生成的真实 schema，记录 React
控件发出的请求，再交给实际后端生成器验证；完成或失败后移除本次创建的 harness。

## 有交叉证据的无效模型参数

对比签名包含块位置、尺寸、结构、材料绑定、导热张量、密度、比热和功率，排除名称、
颜色及 metadata，避免把“只更新了说明”误判为真实联动。
以下每项在原生 setter 后能够读回变化；当前 PackStudio 接受修改，但物理签名完全不变。
历史 FloXML 扫描则记录了相应属性的语义变化。详细 diff 路径、哈希在 JSON 中。

| 家族 | 字段 | 本次修改举例 | 缺失效果 |
| --- | --- | --- | --- |
| Chip Array | `vias.plating` | 0.025 → 0.0275 mm | 过孔镀层与等效物性没有重算 |
| Wirebond PBGA | `vias.plating` | 0.025 → 0.0275 mm | 同上 |
| Wirebond PBGA | `bond_wire.total` | 121 → 122 | 键合线数量不进入模型或等效物性 |
| PQFP | `bond_wire.count` | 32 → 33 | 同上；历史数量探针为 30/31 |
| SOP | `bond_wire.count` | 8 → 9 | 同上 |
| PQFP | `bond_wire.length_x`、`length_y` | 2 → 2.2 mm | 用户输入未参与键合线几何 |
| QFN | `bond_wire.length_x`、`length_y` | 2.75 → 3.025 mm | 用户输入未参与键合线几何 |
| PQFP、SOP | `flag.coverage` | 60 → 66% | 承载台材料仍采用固定审核张量 |

关键 DLL 证据位于 `flopackrealise.dll`：

- RVA `0x7cb0` / `0x478a0` 引用 ChipArray/ThermalVias 镀层厚度 getter。
- RVA `0x2080` 引用 QuadBondWires 两向长度，`0x34cd0` / `0x35770` 引用 QFN 两向长度。
- RVA `0x2cd0` 是键合线数量 getter 的转发入口；`0x4d9c0` 引用 WB 键合线数量。
- RVA `0x9620` 的共用承载台材料流程读取覆盖率，除以 100，并参与材料计算。

当前源码中对应 builders 没有消费上述字段，或仍使用固定家族等效材料。
ADR19 允许保留审核等效模型，但没有明确规定这些仍标为 implemented、可编辑的输入应被
静默忽略。等效表达本身不算差异；**改变已开放参数却不重算等效效果**需要修复或明确收缩能力。
这些证据并不等于本次已运行原生完整几何；历史 FloXML 是交叉证据，不能冒充本次新导出。

## 前端联动缺陷

### 切换 Footprint 丢失独立顶盖选择

CBGA/PBGA 均可复现：先选择 lid，再切到 `*_100_9X9mm`，最终值变为 bare_die。
`WizardFields.tsx` 清除了所有 `preset_values` 目标；当前真实预设包含 `cover.type`，因此独立
开关也被清除。现有 synthetic 前端夹具没有把 cover.type 放进 preset_values，未覆盖此情况。
requirements.md 明确要求切换源规格保留独立分支开关，因此不能归入既定取舍。

### 隐藏参数导致正常切换后无法生成

先选择 lid，将 lid.length 改为 6.1 mm，再选择 plate。
前端保留 `lid.length` 的显式覆盖；后端报
`parameters are inactive in the current branch: ['cbga_fc.lid.length']`，PBGA 同样如此。
后端拒绝无效分支本身符合要求；前端没有清理或隔离隐藏覆盖导致正常用户操作失败。

## WB 默认去球与背面结构

原生 `setDieTypeData` RVA `0x40660` 在存在中央去球区时启用 backsideSpreader，并推导底层
开孔；`setLayerData` 设置扩散结构尺寸和厚度。36 个 WB 默认分支中有 29 个启用该结构。
例如 `PBGA_192_17X17mm` 的扩散结构为 9.4 × 9.4 × 0.018 mm。

当前 `pbga_wb.py` 生成实心 bottom-trace，没有创建 backsideSpreader，也没有消费其尺寸或
底层开孔参数。库中的有效参数存在，生成器没有跟随对应默认拓扑。
ADR19 已说明完整预设不代表完整几何复刻，因此将这一项单列为“未实现结构差距”，而不与
11 个已开放参数的无效效果混为一谈。没有找到明确删除 backsideSpreader 的专项决策。

## 一致、允许不同与待确认

### 已确认的一致行为

- 416 份原生初始化快照一致，默认值来源及 DES 哈希一致。
- CBGA/PBGA 各四个顶盖选择，在默认 Footprint 下已绑定尺寸与 PACK 一致，没有发现
  “切换顶盖时必须重新套一组尺寸而项目遗漏”的证据。
- 56 个组件材料控件中22个可切换、34个只有一个选材；均核验显式选材绑定，包含条件
  分支内的材料控件。只有可切换控件要求更换材料后产生模型差异。
- 36 个项目 BGA 控制探针覆盖表达方式、中央区、去球、显式坐标和允许非对称；2 个
  Chip Array 去球范围过大的输入被正确拒绝，属于预期校验。
- WB 直接 setData 修改 D 为 24 mm，并不会重新执行向导厚度规则；修改球间距不会自动
  改过孔间距；修改球列数不会自动改已存键合线数。本次只观察到被修改字段变化。
  因此这些初始化规则不能擅自提升为“任何编辑都必须自动重算”的规则。

### 明确取舍，不计作缺陷

依据 requirements.md、ADR5/6/9/12/19：固定 standard outline/actual die、两层生产模型、
有厚度的 bumps+underfill 等效层、项目中央焊球/去球优先级与静态空气、矩形归一化与
PTA/ECXML 表达、常量温度参考张量、移除求解器边界和网格实体、项目 Bare Die 尺寸预设。
以上能力边界不要求复制 PACK 的所有分支和输出格式。

SOP `bond_wire.length` 在已归档默认 standard-outline/orthotropic-cuboid 分支中，PACK 自身
改变输入后 FloXML 也不变，本次项目无变化与此一致。
Bare Die `die.flipped` 的归档差异是监控点位置和面热源 attachment/collapse；当前项目使用
体积均匀热源且没有监控点输出，因此不把当前物理签名不变算作几何联动缺陷。
SOP `package.length` 本次仅确认项目无变化，缺少对应原生几何差异证据，保持待确认。

## 覆盖限制

原生编辑重放路径是 `loadDESPackage → initialise → setWizardData → getData → 属性 setter
→ package.setData → getData`。它覆盖参数对象、组状态和 setter 行为，没有重放 PACK GUI
事件、完整 realise、导出或任意多参数组合。原生 `groupValid` 多为未赋值检查，不能与完整
几何合法性混用；PBGA FC 的未采用显式 built-up/core-via 数据在默认状态也可能返回 false。

每个生产字段只选一个活动上下文、一个扰动；不是完整上下界或组合穷举。顶盖四选择仅对
两类默认 Footprint 检查。4 个金属表字段、2 个 vias 组启用字段、Bare Die 的9字段没有独立
DLL 对照；Bare Die 没有 DES 预设。材料与项目 BGA 探针只验证本项目联动，未宣称复刻 PACK。
子类型的完整默认目录已包含在 416 份快照中，前端 subtype 路径沿已有测试核验。

## 验收

- 后端：588 passed，包含实际启用的原生 catalog/material/default/interaction 测试。
- 前端：22 passed；真实 schema 研究 harness 另有 3 passed（用于记录观察，不代表缺陷修复）。
- `uv run --locked ruff check .`、`npm run lint`、`git diff --check` 通过。
- 原始系统 pytest 临时目录 WinError 5；改用仓库 `tmp/` 中新建的专用 basetemp/cache 后通过。

```powershell
$env:PACK_NATIVE_INSTALLATION = 'E:\Program Files\Siemens\SimcenterFlotherm\2504'
uv run --locked pytest --basetemp tmp/pytest-pack-interaction-20261012 -o cache_dir=tmp/pytest-pack-interaction-cache
```

后续复验使用新的专用临时目录名。优先修复两类前端转移，再补齐11个开放参数的物理效果；
WB backsideSpreader 的支持范围应作为独立结构工作记录，保留项目表达取舍。
