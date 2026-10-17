# FloXML 导出与 PACK 自动差异验证

2026-10-17。结果见 [自动报告](../validation/floxml/report.md)、
[机器结果](../validation/floxml/results.json)、[完整证据包](../validation/floxml/evidence.zip)。
导出功能提交 `6824c99`；验证器版本由结果中的源文件 SHA-256 定位。

## 结论与范围

FloXML 已接入后端、API、前端选择和下载。它使用真正的 FloTHERM `xml_case`，
与 `neutralXML` ECXML 独立；生产只消费 PackageModel，不加载 PACK、XSD 或研究文件。

实际矩阵为 **413 案，412 案成功比较、1 案为已知生成缺陷**。
382 案复用仓库真实 PACK 输出：八基准、320 个已映射数值单变量、6 个顶盖选项、
48 个顶盖条件数值分支。另有本机 PACK 新生成的 31 案：八重复基准、七组合/边界、
八材料编辑、八非零功率。八重复基准文件与归档逐字节一致。
案例共享基准和公式，数量不代表 413 个独立物理实验，也不代表完整规格笛卡尔积。

成功导出的文件通过五份安装 XSD，并逐块核对坐标、尺寸、层级、材料引用、三向导热率、
密度、比热与功率。原生对照按区域交叠体积比较材料，不按名称或块数量要求相等。
**这证明格式与当前模型保真；不能证明当前模型没有物理缺陷或已满足实际热仿真精度。**

## 五类归因

| 类别 | 重要差异 | 证据与状态 |
| --- | --- | --- |
| 明确功能取舍 | C1 有限厚度正交 bump；C2 静态空气/既定 BGA 分区；C3 体块与原生 collapsed；C4 参考温度常量；C5 体热源与原生面源 | 需求、ADR9/25、逐案原生 XML、项目输出；已记录，保持现有选择 |
| 有物理依据的不同实现 | P1 QFP 小高差仍保留竖直线段；P2 键合线按并联导热率和质量加权比热重算 | `qfp-small-height`、四个 `*-gold-edit`；规则与几何可解释，仍不声称温度场等价 |
| 已确认实现缺陷 | F1 QFP/SOP 等效引线和 QFP 连筋最终被纯金属覆盖 | 八基准及单变量、矩形 QFP；默认 QFP 内引线 `(151.09,0.68,151.09)` 被绑定为 `(301.5,301.5,301.5)`；保留待修 |
| 已确认实现缺陷 | F2 bump/BGA 组分编辑不传播，WB 铜编辑只影响部分衍生材料 | 四个 constituent_material 案，原生 `.mat`、`.des` 回读已验证；保留待修 |
| 已确认实现缺陷 | F3 QFP 负高差无法生成 | `qfp-negative` 的 `flag.downset=0.44 mm`；PACK 有输出，项目报负高度；保留待修 |
| PACK 继承的物理风险 | R1 WB 不等铜厚的 Via 端部间隙 | `wb-copper-asymmetry`，两侧原始几何一致；已确认，几何含义待决策 |
| PACK 继承的物理风险 | R2 Chip Array/SOP 的 die 与 die_attach 同底面重叠，差集后硅变薄 | 两基准与加厚胶案例；已确认，裸硅厚度/包络高度的字段语义待决策 |
| 证据不足 | U4 原生求解器的重叠优先级与 collapsed 实际行为；U5 厚度字段含义；U6 全规格/组合覆盖与热精度 | 已列为 open；没有以数字匹配、XSD 或测试通过关闭这些物理问题 |

每个重要属性差异交叠区在证据包的 `comparison.json` 中有原生路径、项目路径、
结构角色、数值、交叠体积、category 和 attribution。未知差异默认归为证据不足，
不能自动归入“物理合理”。`findings` 可在同案包含多种归因。

### F2 的独立输入响应检查

`fc-solder-edit` 中物理焊料导热率从 36 改到 72，项目法向均质化自身应得到
`12.8124178421 W/(m·K)`，实际仍为 `6.6548962410`；PACK 此例也输出前者。
这是按项目并联式得到的输入响应缺陷，不依赖是否采用 PACK 面内公式。
同一 bump 区域的面内差异还包含 C1 的既定网络近似，机器结果保留双重归因，不能把全部
三向数字差异都称为 F2，也不能要求修复 F2 后面内值必须变成 PACK 的标量。
`cbga-underfill-edit`、`wb-ball-edit` 同样保留旧衍生值。
`wb-copper-edit` 的 Via 随铜变化，但顶铜、底铜和 flag 部分仍冻结。
每案另记录 `project_material_sensitivity`，与移除 custom_materials 后的项目基准比较。
四个 gold 编辑案则证明已接入的键合线组分确实参与重算。

### 两项原生风险的数值含义

WB 的例子 `A1=0.6, A2=0.36, t_top=0.01, t_bottom=0.04 mm`，Via 覆盖
`0.61–0.92 mm`，flag 从 `0.95 mm` 起，留下 `0.03 mm` 间隙。
PACK 新输出与项目都保留这一表达，不能称为新增导出兼容性错误。

Chip Array 默认输入硅厚 `0.3 mm`、胶厚 `0.025 mm`，差集后的硅厚是 `0.275 mm`；
胶改到 `0.2 mm` 后硅厚为 `0.1 mm`。SOP 相应是 `0.342` 和 `0.18 mm`。
**PACK 实际存在 Chip Array die_attach**，其底面与 die 相同；旧 v4 报告“没有胶层”
的文字已勘误，本验证采用原始 XML 与最新审查结论。

## 比较方法与数值边界

1. 原始输入使用独立 `reference_inputs.json` 和 manifest 的明确字段；不假定当前默认值
   等于旧归档输入。条件顶盖分支单独建立请求。完整请求随每案保存。
2. 原生解析器累积 assembly 平移和继承材料，m 转 mm；名称只用于追踪。
   isotropic、orthotropic、biaxial 和温度材料参考点可读取。
   旋转、孔、曲线、未知实体/源/thermal 属性显式拒绝；region/monitor 记录为非物理控制项。
3. 原始 cuboid 按六个几何数值匹配 builder，记录结构角色、材料和优先级。
   builder 材料是原始表达检查，不冒充最终 `generate()` 的材料绑定。
4. 对 PACK 采用声明的项目优先级独立执行矩形差集，逐交叠区与导出分区比较。
   这对齐了分析约定，**没有反证 FloTHERM 求解器采取相同优先级**。
5. 所有 PACK 原始重叠方块禁止直接累加作为物理总体积。collapsed 固体使用名义包络，
   报告状态为 provisional；其质量/热容量不能直接解释为求解器实际瞬态储热量。
6. 无重叠对照分区计算 `V`、`rho*V`、`rho*cp*V`，长度由 mm³ 转 m³。
   总量及按结构角色的分量、导热张量不同区域体积、结构绑定不同区域体积均保留。
   热源几何不含材料，不计入实体质量；面源与体源分别保留原始位置/尺寸/collapse。

容差：几何匹配绝对 `1e-7 mm`（相对 `1e-10`），裁剪轴长 `1e-10 mm`，
交叠记录阈值 `1e-12 mm³`；属性相对 `1e-7`、绝对 `1e-8`；总功率 `1e-10 W`。
小于阈值的体积残差不作为缺陷。所有数值必须有限。
不由整体质量相等推断局部材料场正确；不同交叠区仍单独记录。

## 原生生成与来源

本机 `flopack.exe` 文件版本 `2025.13.1.1142`，SHA-256
`de21140177f9836147fdac1f9a82bb68490d92844fb321087201667575976ba1`。
XSD 来自安装 `XML_PLUGIN_SCHEMA`，原样归档在 `output_format/floxml/`。
既有研究使用用户提供的 v3/v4 证据及 2026-10-17 项目审查，未重复反编译整套算法。
本次新增原生导出以实际生成文件、日志和回读为准，不把旧研究的 900 项复算计入新案例。

原生运行创建隔离 config、central、user 目录，隐藏启动进程；不改写安装材料库。
内置材料不可直接修改时，在隔离库创建自定义材料，显式写入 k/rho/cp，再由 DES 指定。
导出后检查 `.mat` 三种物性和 `.des` 的选材/数值键；命令 ERROR、缺文件、超时或回读
不一致均使原生批次失败。绝不只凭进程退出码或文件能解析认定输入已应用。
八个功率案的原生与项目总功率均为 `2.5 W`，同时明确保留面源/体源分布差异。

证据包只包含输入、输出、比较、`.des/.mat` 和执行日志；不含安装配置或许可证文件。
`results.json` 记录来源/输入/输出 SHA-256、实际软件版本、源代码/默认库指纹与证据包指纹。

## 可重复命令

在仓库根目录执行。新原生运行须使用不存在导出文件的新目录，防止混用陈旧结果。

```powershell
uv sync --locked --python-preference only-managed
uv run --locked pytest tests/backend/exporters/test_floxml.py tests/backend/test_floxml_comparison.py
uv run --locked ruff check .
npm test
npm run build
npm run lint

# 382 个归档案例，不需要 PACK/许可证
uv run --locked python -m tools.floxml_validation.run --output tmp/floxml/archive-recheck

# 413 案，包含本机重新生成的 31 案
uv run --locked python -m tools.floxml_validation.run --output tmp/floxml/all-recheck --native-dir tmp/floxml/new-native --installation 'E:\Program Files\Siemens\SimcenterFlotherm\2504'

# 可重用已完成的原生目录，省去 --installation 即只检查回读并比较
uv run --locked python -m tools.floxml_validation.run --native-only --native-dir tmp/floxml/new-native --output tmp/floxml/native-recheck

# 封装全量结果：archive-output 可为包含全部案例的结果目录
uv run --locked python -m tools.floxml_validation.report --archive-output tmp/floxml/all-recheck --native-output tmp/floxml/native-recheck --destination tmp/floxml/delivery
```

完全脱离 PACK 安装重放交付证据：

```powershell
Expand-Archive docs/validation/floxml/evidence.zip tmp/floxml/unpacked
uv run --locked python -m tools.floxml_validation.run --evidence-dir tmp/floxml/unpacked --output tmp/floxml/offline-recheck
uv run --locked python -m tools.floxml_validation.verify --replay-output tmp/floxml/offline-recheck
```

可加 `--baselines-only` 快速检查八基准，或重复使用 `--case CASE_ID` 筛选明确案例。
每案在输出目录生成 request、FloXML、comparison、result；已知 F3 记录拒绝原因。
离线重放先验证证据指纹，仍要求同一版本源码/默认库；不把历史结果绑定到任意未来模型。

## 实际验收

- 后端全量：620 passed、25 skipped；后补验证器 3 项及包含本机 PACK 集成的定向 29 项通过。
- 前端 32 项通过；生产构建与 ESLint、Ruff 通过，保留既有大 chunk 提示。
- 验证器使用解析几何体积/质量/热容量已知值、拆块/重命名不变性、属性/坐标/功率扰动和
  嵌套位移测试；不是仅断言“当前输出等于当前实现”。
- 八类 FloXML 导出/API 经 XSD 与逐字段回读；原生批次的 DES/MAT 回读和零 ERROR 已检查。
- 证据包已完整解压并离线重放 413 案；412 份导出字节、原始映射、物理指标和功率一致，
  QFP 负高差的拒绝也一致；指纹/ZIP 完整性校验记录在 `replay-check.json`。
- 本次未修复原有 F1/F2/F3，也未验证实际 FloTHERM 导入、网格、求解和测量精度。
