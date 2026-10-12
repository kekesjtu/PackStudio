# PACK 已开放参数的等效材料联动

日期：2026-10-12。对应 TASK22；范围为参数审计确认的11个实现缺口。

## 结果

11项已经接入生产生成器，按 PACK 保留分支重算等效导热率、密度和比热。
相应 FloXML 单变量扫描只改变材料，不改变 cuboid 位置/尺寸；因此本次保留原始几何包络，
没有把“键合线长度”误当成矩形包络的端点坐标。

| 模板 | 参数 | 实际效果 |
| --- | --- | --- |
| Wirebond PBGA | `bond_wire.total` | 重算键合线金属体积分数及两向正交张量 |
| PQFP | `bond_wire.count` | 按芯片周长分配每侧线数，取整后重算两向物性 |
| SOP | `bond_wire.count` | 重算键合线体积分数及两向物性 |
| PQFP | `bond_wire.length_x` / `length_y` | 分别重算对应方向的线体积和等效物性 |
| QFN | `bond_wire.length_x` / `length_y` | 分别重算对应方向的线体积和等效物性 |
| Chip Array、Wirebond PBGA | `vias.plating` | 按镀层截面积重算过孔物性 |
| PQFP、SOP | `flag.coverage` | 重算承载台导热率、密度和比热 |

共1+1+1+2+2+2+2=11项。计算还会消费其必要的芯片尺寸、直径、塑封材料和金属材料等输入；
Chip Array 键合线按保留的球数联动，避免恢复等效张量后继续冻结家族基线。

修复同时纠正组件选材覆盖计算结果的行为：键合线选材是金属组分，承载台选材是金属组分，
塑封选材是基体。它们参与混合，而不是把整个等效 cuboid 改成纯金属。
SOP tie bar 虽复用承载台的原始材料 ID，但属于另一个组件，仍按其选材直接绑定。
自定义物理组分会参与重算；API 显式覆盖生成后等效材料时仍保留用户覆盖优先级。

## DLL 与来源

本机 PACK 2504，`flopackrealise.dll` SHA-256：
`838ed6c2e7d40cc749b8b145f55d78e9e95495fef974d593a7641fc0aa528edd`。
研究工具使用现有七 DLL 哈希守卫；生产读取独立 JSON 与手写公式，不加载 DLL。

- `0x1ccf0`：线体积 / 等效 cuboid 体积；输出比热、密度、并联导热率。
- `0x1ce70`：体积分数转换为质量分数。
- `0x1ceb0`：线性混合。
- `0x2080`：PQFP/SOP/Chip Array 的线数分支、PQFP 每侧取整和两向长度输入。
- `0x34cd0` / `0x35770`：QFN 两向张量与保留的单步矩形包络。
- `0x4d9c0` / `0x4eeb0`：WB 键合线体积分数和材料生成。
- `0x9620`：承载台覆盖率、质量混合与 `coverage * metalK`。
- `0x7cb0` / `0x1d350`：Chip Array 镀层、内孔空气和等效材料。
- `0x478a0`：WB 空心过孔的镀层面积、密度及金属比热。

完整有界反汇编见 [pack_material_rule_disassembly.json](../validation/pack_material_rule_disassembly.json)。
数值、源 FloXML 路径/哈希、期望值和实际值见
[pack_material_couplings.json](../validation/pack_material_couplings.json)。
FloXML 是既有归档；本次没有新运行 FloSCRIPT 或完整原生 realise。
原生数学探针直接调用审核构建中的两个局部纯数值函数，材料缓冲区仅提供已经逆向确认的
`density(+0x40)`、`specific_heat(+0x48)`、`conductivity(+0x60)` 只读输入。

## 公式

所有长度使用一致单位；生产用 mm，DLL 本体用 m，以下体积分数中的长度比保持一致。
记金属体积分数为 `f`，金属与基体物性分别为 `rho_m/c_m/k_m`、`rho_b/c_b/k_b`。

```text
rho = f*rho_m + (1-f)*rho_b
mass_fraction = f*rho_m / rho
specific_heat = mass_fraction*c_m + (1-mass_fraction)*c_b
parallel_k = f*k_m + (1-f)*k_b
```

键合线 X 类等效材料的 x/z 使用并联导热率，y 使用基体导热率；Y 类反之。
这里没有套用一般复合材料的横向混合公式，因为 PACK 该 cuboid 分支的横向值就是基体值。

### SOP / WB

`f = N*pi*d / (8*(Ld+Wd))`，`d` 是线直径，`N` 是总数。
SOP 已开放的独立 `bond_wire.length` 在此分支不进入公式，保留 PACK 的默认无输出变化行为。

### PQFP

```text
Nx = floor(N*Wd / (2*(Ld+Wd)))
Ny = floor(N*Ld / (2*(Ld+Wd)))
H = dieThickness + dieAttachThickness - flagDownset
Sx = (flagLength-Ld)/2 + leadGapX + H
Sy = (flagWidth-Wd)/2 + leadGapY + H
fx = Nx*pi*d^2*wireLengthX / (4*Sx*Wd*d)
fy = Ny*pi*d^2*wireLengthY / (4*Sy*Ld*d)
```

在默认方形芯片上，32和33都产生每侧8根，因此物性可以相同；31产生每侧7根，物性变化。
这修正了“任意+1必须改变输出”的判断标准，但不掩盖原生成器完全未消费数量参数的问题。
实测例如 PQFP X 张量：32根时 `k_x=54.88830513924264`；30/31根时约 `48.11226699683731`。

### QFN

X 方向使用左右引脚数和其 Y 包络，Y 方向相反。

```text
Tx = (leftRightLeadCount-1)*pitchY + leadWidth
Sx = (packageLength-Ld)/2 - leadLength - leadEtch
fx = leftRightLeadCount*pi*d^2*wireLengthX / (4*Sx*Tx*d)
```

Y 方向交换轴。没有引脚的方向不产生键合线。当前项目保留单步等效包络，没有开放 PACK
多步离散线选项；没有用本次公式宣称那些分支也已复刻。

### 镀层与承载台

镀层比例 `f = 1 - ((D-2*t)/D)^2`；拒绝 `t>D/2`，不把负内径取平方当合法物理几何。
Chip Array 的保留分支以金属壳+内孔空气混合；原生 filledVias=yes 时按实体金属计算。
WB 对离散空心过孔采用 `k=f*k_m`、`rho=f*rho_m`、`specific_heat=c_m`。
金属按对应预设的 `metalLayers/materialOfMetal` 从独立原生库按名称读取。

承载台 `f=coverage/100`；密度和比热使用上述混合，导热率为 `f*k_m`，没有额外加入塑封导热。
因此60%→66%不是换成纯金属，也不是缩放几何厚度。

## 关于原来的13个候选

- 11项：本次已修正生成器缺口。
- SOP `bond_wire.length`：PACK 默认 standard-outline/orthotropic-cuboid 输出也不变，属于已确认一致行为。
- SOP `package.length`：本次没有新增支持该字段几何效果的原生证据，继续待确认。

Bare Die 翻转是后续去掉 metadata 后扫描发现的另一项，不在原来的13个候选中。
其已归档差异为监控点/面热源方向，项目使用体积均匀热源，前次审计已单独说明。

## 验证与限制

- 11项 × 两个归档数值，共22个用例；涉及材料的 x/y/z 导热率、密度、比热以 `1e-11` 相对精度匹配。
- 3个 PQFP 组合输入+4个镀层厚度：直接 DLL 数值调用与生产公式匹配。
- 后端完整623项通过；最终补充显式等效材料覆盖后，相关27项通过。
- 342个源预设、510组生成/PTA/ECXML 导出与 XSD 验证通过，未改变几何分区或输出格式。
- 原生材料温度依赖仍沿 ADR19 在参考温度投影为常量；没有穷举任意材料/任意参数组合。
- 没有修复前次单列的 WB backsideSpreader 未实现结构；这属于独立几何范围。

```powershell
uv run --locked python -m tools.verify_pack_material_couplings 'E:\Program Files\Siemens\SimcenterFlotherm\2504'
$env:PACK_NATIVE_INSTALLATION = 'E:\Program Files\Siemens\SimcenterFlotherm\2504'
uv run --locked pytest tests/backend/templates/test_pack_material_couplings.py tests/backend/test_pack_formula_probe.py
uv run --locked python -m tools.validate_catalog_presets
```
