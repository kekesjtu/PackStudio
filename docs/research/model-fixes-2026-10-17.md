# 三项建模缺陷修复与结论边界

日期：2026-10-17。模型版本 2.2。

## 修复结果

| 缺陷 | 修复内容 | 验证证据 |
| --- | --- | --- |
| F1 等效引线/连筋被纯金属覆盖 | 重算当前 B/e、基体/金属与 QFP 连筋实际几何修正，保护最终等效材料绑定 | 默认 QFP 内引线恢复 `(151.09,0.68,151.09)`；SOP 引线恢复混合物性；变节距/宽度、矩形连筋、组分 rho/cp/k 测试通过 |
| F2 物性覆盖未进入部分衍生材料 | bump/BGA 在计算前读取当前物性；WB 两铜层、flag、Via 使用同一当前铜物性；保留显式衍生覆盖优先级 | 焊料 36→72 时 bump kz 从 6.6548962410 正确变到 12.8124178421；WB 铜 k=100 时顶层 k=30.14、flag k=60.08；密度/比热亦有独立加权检查 |
| F3 QFP 负高差被拒绝 | 位置按符号、长度按绝对值；名义体积分母同步更正；零高差省略零厚度竖段 | ddf=0.44 mm 的原始几何和物性匹配实际 PACK；正/零/小/负高差六点、功率守恒和无重叠测试通过 |

独立测试覆盖三类 bump（含 Bare Die 可选 bump）、四类 BGA 的等效/离散模式、
去球、关闭 Via、物理材料 rho/cp/k 编辑和显式衍生材料优先级。
没有通过冻结默认张量或只改材料 ID 来规避重算。

## 完整对照

[机器结果](../validation/floxml-model-fixes/results.json)、
[汇总表](../validation/floxml-model-fixes/report.md)、
[完整输入/输出/比较证据](../validation/floxml-model-fixes/evidence.zip)、
[验签记录](../validation/floxml-model-fixes/replay-check.json)。

复用同一批有明确输入和指纹的真实 PACK 输出，重新生成当前 PackStudio 模型。
413 案全部完成比较（修复前为 412 案比较、1 案 QFP 拒绝）；原生 cuboid 均有几何映射。
F1/F2/F3 对应的缺陷表现消除；所有剩余交叠区属性差异均有归因。
413 个成功输出通过 XSD 与逐块/材料/功率回读，八类 2.5 W 案例守恒。
独立测试 25 项和分类回归 2 项通过；全量后端 650 passed / 25 skipped，前端 32 passed。

作为影响量级的例子，项目声明分区下 QFP 默认计算质量由 224.4877 mg 变为
182.3756 mg，与对照名义分区一致；SOP 由 100.0374 mg 变为 68.6790 mg。
这些不是实测质量；PACK collapsed 实体的名义包络限制仍然适用。

### 保留的差异

- Flip-chip bump 的面内网络与 PACK 标量不同；法向、密度、比热符合当前组分输入。
- SOP 独立实体连筋保留纯金属，PACK 对其复用等效 die_flag 材料。ADR22/26 已区分
  实体连筋与引线包络；这两处区域归为 P3，不冒充尚未修复的 F1。
- QFP 小高差保留有限竖段；Chip Array 保留声明的静态空气。
- 原始重叠分区、collapsed、温度材料常量化、面源/体源按既定范围记录。

## 能否据此说“没有大的建模缺陷”

**不能从 FloXML 对照单独推出这个结论。** 当前可以支持的表述是：

> 在这 413 个明确输入案例及项目声明的几何分区、材料近似和源项假设下，三项确认的
> 实现缺陷已修复；本轮未发现新的未归因几何或材料实现差异。

这与“所有工程用途下没有重大物理建模缺陷”有不同证据要求，原因具体如下。

1. **双方会共享风险。** WB 不等铜厚的 Via 端部间隙、Chip Array/SOP die 与胶层
   同底面重叠仍在。匹配 PACK 无法排除这些结构对实际热路径/硅质量的影响。
2. **材料库需要独立核实。** 原生材料库与输出存在低值：SOP 所选金属的库内比热为 1，
   部分附件材料在原生导出中的密度/比热为 1。报告 R3 列出导出中待核实的具体材料和值。
   低值本身不自动证明错误，但在确认是真实数据还是占位值前，不能据此保证瞬态储热可靠。
3. **分区和源项尚非求解器验证。** 当前对照采用声明的项目优先级；没有验证原生
   collapsed 实体的实际求解行为，也没有证明面热源与体热源给出相同温度场。
4. **覆盖有限。** 案例相关、共享基准；不等于所有 346 规格与全部组合、各向异性组分、
   温度/功率工况都验证。也没有下游网格收敛、热阻/温升或实验验证。

要进一步形成工程可信结论，应先确定上述几何含义与材料数据，再选代表工况做独立
能量/热阻检查、网格收敛及高保真或实验对照。当前修复不擅自更改这些已声明假设。

## 复现

在本次提交的源码下，可完全脱离 PACK 安装重新生成并比较：

```powershell
Expand-Archive docs/validation/floxml-model-fixes/evidence.zip tmp/model-fixes-evidence
uv run --locked python -m tools.floxml_validation.run --evidence-dir tmp/model-fixes-evidence --output tmp/model-fixes-replay
uv run --locked python -m tools.floxml_validation.verify --delivery docs/validation/floxml-model-fixes --replay-output tmp/model-fixes-replay
uv run --locked pytest
uv run --locked ruff check .
npm test
```

同一版本源码允许 Git LF/CRLF 检出差异；原生文件、导出文件、XSD 和 ZIP 仍严格校验字节。
修复前的 [历史报告](floxml-validation.md) 和证据保持原样，用于追踪前后变化。
