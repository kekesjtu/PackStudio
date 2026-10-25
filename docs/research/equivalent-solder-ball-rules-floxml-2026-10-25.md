# 非离散焊球阵列的等效方式：原生 FloXML 反推

日期：2026-10-25。只分析原生输出，不修改 PackStudio 的生产实现或产品选项。

## 范围与结果

原生归档选项显示：Chip Array 仅有 Discrete Cuboids；Flip Chip PBGA/CBGA 支持
Orthotropic Cuboid；Wirebond PBGA 另外支持 Isotropic Cuboid。
因此本研究有三个正交等效配置和一个 WB 各向同性配置，不强行给 Chip Array 添加原生选项。

正式新导出共 172 份：四份基线、136 份首次变参、32 份原生保存 DES 重载输出。
168 个变参/重载方案的 7092 个几何及物性数值核验通过。
最大几何误差 `8.881784197001252e-16 mm`，物性最大相对误差 `2.1615104696064513e-15`。
通过是指公式成功重建原始输出，不表示所有边界组合都具有合理的物理等效性。

证据仅为真正导出的 FloXML、输入及保存 DES、CSV 载荷和已有组分材料 JSON。
没有引用生产混合实现或 DLL 数值探针/反汇编计算规则。
逐例原始数值、预测输入、误差、模式归一化、软件指纹和源文件哈希见
[验证报告](../validation/equivalent_solder_balls_floxml_2026-10-25.json)。

## 1. 普通完整阵列：一个连续包络

设 MD/ME 为候选列数/行数，e 为球间距，b 为直径，A1 为球层高度，尺寸单位一致。

```text
Lx = (MD-1)*e + b
Ly = (ME-1)*e + b
size = (Lx,Ly,A1)
origin = (-Lx/2,-Ly/2,0)
N = MD*ME
phi = N*pi*b²/(4*Lx*Ly)
```

外包络按直径 b 扩展，不是按离散等面积正方形柱的边长 `b*sqrt(pi)/2` 扩展。
原始几何只有一个 `solder_ball`，其中把焊料和剩余空气均匀化。
分子是参考圆柱截面积总和，乘 A1 后与包络体积相比，所以 A1 在体积分数中约去。
这不是用真实球体积 `pi*b³/6` 构造的体积分数。

## 2. 等效物性

已用两种焊料验证组分替换：

| 组分 | k / W/(m·K) | rho / kg/m³ | cp / J/(kg·K) |
| --- | ---: | ---: | ---: |
| Solder (Sn63/Pb37) | 50.9 | 8400 | 150 |
| Solder (Pb90/Sn10) | 36 | 10750 | 142 |
| 空气 | 0.0261 | 1.1614 | 1007 |

焊料来自材料 JSON。空气值由四个新完整阵列基线独立反算：

```text
rho_air = (rho_eff-phi*rho_solder)/(1-phi)
cp_air = (rho_eff*cp_eff-phi*rho_solder*cp_solder)/((1-phi)*rho_air)
k_air = (kz-phi*k_solder)/(1-phi)
```

四个基线一致给出表中空气常量；报告保留未舍入的反算值。
随后用其余变参正向计算，未用各例输出去拟合自己的 phi。

```text
rho_eff = phi*rho_solder + (1-phi)*rho_air
cp_eff = (phi*rho_solder*cp_solder + (1-phi)*rho_air*cp_air)/rho_eff
k_parallel = phi*k_solder + (1-phi)*k_air
```

正交等效的导热张量为 `(kx,ky,kz)=(k_air,k_air,k_parallel)`，
原生 XML 用 biaxial 材料记录面内与法向导热率。横向值直接是空气导热率。
WB 各向同性等效的三个方向均为 k_parallel；几何、密度、比热与正交配置相同。
比热按质量加权，密度和体积热容按体积分数线性混合。

## 3. Staggered：连续减半

几何包络不变，PACK 直接使用 `phi_staggered=phi_full/2`。
没有先统计棋盘格筛选后整数个球，再代入完整包络。
例如 5×5 的离散模式有 13 球，但等效物性相当于 12.5 个参考圆柱。
4×6 的连续减半与离散 12 球恰好一致。

## 4. 中央去球：四块边框及公共材料

正常中央空区分支 `MDp<MD` 且 `MEp<ME`，使用实数除法，不取整：

```text
rx = MDp/2
ry = MEp/2
Tx = (rx-1)*e+b
Ty = (ry-1)*e+b
Linner = Lx-2*Tx
Winner = Ly-2*Ty
Aframe = Lx*Ly-Linner*Winner
Nframe = MD*ME-(MD-MDp)*(ME-MEp)
phi_frame = Nframe*pi*b²/(4*Aframe)
```

左右两块尺寸为 `Tx×Ly×A1`，上下两块为 `Linner×Ty×A1`；位置使四块互不重叠。
四块共同绑定一个按整个边框计算的 Solder_ball 材料，没有逐块分别统计球数配材料。
若主阵列 Staggered 开启，phi_frame 继续乘 0.5，四块尺寸不变。

奇数参数在这里参与连续几何和数量计算。因此在 5×5、b=0.5、e=0.8 下：

| MDp、MEp | 每侧边框宽度 Tx、Ty / mm | 参数球量 Nframe | phi | kz |
| --- | --- | ---: | ---: | ---: |
| 2、2 | 0.5、0.5 | 16 | 0.490873852 | 24.998767266 |
| 3、3 | 0.9、0.9 | 21 | 0.409061543 | 20.836656055 |

这与离散模式的每侧 `floor(MDp/2)`、`floor(MEp/2)` 不同。
离散模式 (2,2)/(3,3) 都是外围 16 球；非离散模式的几何与物性均不同。

## 5. 中央加球：独立等效块

Central Balls 开启时另建 Center_SBall 下的 `center_sball`，材料为 centerSolder：

```text
Lcx = (MDc-1)*e+b
Lcy = (MEc-1)*e+b
phi_center = MDc*MEc*pi*b²/(4*Lcx*Lcy)
```

高度仍为 A1，块在原点居中。中央阵列自己的 Staggered 开启时 phi_center 直接减半，
不按离散棋盘格保留球数取整。中央等效块使用同一种焊料/空气混合公式及全局等效模式。
例如中央 3×3 在 Staggered 下使用 4.5 球的连续填充量，离散模式实际保留 5 球。

主块和中央块可在空间重叠，PACK 不自动把主块切除中央区域，也不自动合并或去重。
中央去球加中央球通常为四块边框加一个中央块；是否相交仍取决于具体尺寸。
FloXML 只证明这些对象及材料被导出，不证明下游求解器对重叠对象的覆盖优先级。

## 6. 非空显式名单与 CSV：自动切回离散

通过 DES 请求 mode=4（正交）或 mode=2（WB 各向同性），同时提供非空显式网格名单
或启用 CSV 时，原生保存文件的 `radio_BGA_modeling` 均变为 3（离散）。
每种配置均做八个保存重载对照，不能把这些组合当成持久的任意阵列等效支持。

### CSV

初次和重载均输出逐球纯焊料 cuboid。三个任意坐标输入生成三个对象，
不构造统一包络；其他筛选和 Central Balls 不再生效。
空 CSV 为零对象。与此前 CSV 离散研究结论一致。

### 显式网格名单及首次输出差异

强制不兼容输入时，首次 FloXML 已是逐球几何，但引用的是请求等效模式下、
按名义阵列参数算出的混合材料。保存后的 DES 则已经标记离散模式。
将这份原生保存文件放到新进程重载，输出才变为逐球纯焊料；
主阵列与中央阵列也按离散规则表达。

例如显式仅保留一个角球：

| 阶段 | 请求/保存模式 | 几何 | 材料密度 |
| --- | --- | --- | ---: |
| 初次输入 | 请求 4，保存 3 | 一个等面积小柱 | 3012.680944883（名义 5×5 混合物性） |
| 保存后重载 | 请求 3，保存 3 | 同一个小柱 | 8400（纯 Sn63/Pb37） |

四配置共 20 个显式名单案例都出现首次/重载差异。
这只是对实际序列化与导出结果的记录，没有据此推断缓存或内部实现的原因。
应把该首次输出作为强制不兼容输入的特殊行为，不定义成稳定的等效方法。

## 7. 正常公式之外的边界结果

### 达到总行列数时：几何与材料面积分支不同

在 5×5 下，MDp=5、MEp=2 时几何恢复为一个完整 `3.7×3.7×0.4` 块。
材料却仍吻合边框公式的 Aframe=12.88，而不是完整包络面积 13.69。
所以其 kz=19.414816821，与普通完整阵列 kz=18.267639274 不同。
MDp=MEp=5 的类似结果也已验证。不要假设材料分母总等于实际输出块面积之和。

### 极薄边框可得到 phi>1

同样参数下 MDp=MEp=1 的边框宽度仅 0.1 mm，公式产生 phi=1.227184630。
原生未钳制到 1，输出 rho=10308.087042362、kz=62.457768164，均超过纯 Sn63/Pb37。
这是四种配置均可复现的边界探针结果，不属于有效体积分数范围。
本研究不以“匹配原始输出”代替物理合理性验收，也不据此推断所有 GUI 正常交互都会到达这些状态。

## 代表完整阵列数值

统一 MD=ME=5、e=0.8、b=0.5、A1=0.4、Sn63/Pb37：

```text
Lx=Ly=3.7 mm
phi=0.3585638072486524
rho=3012.680944882942 kg/m³
cp=150.211915617605 J/(kg·K)
正交：(kx,ky,kz)=(0.0261,0.0261,18.267639273587) W/(m·K)
各向同性：k=18.267639273587 W/(m·K)
```

Staggered 后 phi=0.1792819036243262、kz=9.146869636794。
更换 Pb90/Sn10 后同一几何 phi 不变，rho=3855.305891917、cp=142.167144676、kz=12.925038546。
仅 A1=0.4→0.5 时上述等效物性不变。

## 复现与验收边界

正式本地数据：`flotherm_pack_data/validation/equivalent_solder_balls_2026-10-25-verified/`。
每个配置保存 inputs、native、reloaded、definitions.json，基线单独保存。
原始数据只保留本地；Git 中提交工具、验证报告和研究说明。

```powershell
uv run --locked --no-sync --cache-dir tmp/uv-cache python -m tools.equivalent_solder_ball_probes --installation 'E:/Program Files/Siemens/SimcenterFlotherm/2504' --output 'flotherm_pack_data/validation/equivalent_solder_balls_recheck'
uv run --locked --no-sync --cache-dir tmp/uv-cache python -m tools.verify_equivalent_solder_ball_floxml --archive 'flotherm_pack_data/validation/equivalent_solder_balls_recheck' --output 'tmp/equivalent_solder_balls_recheck.json'
```

仅核验正式归档，无需启动 PACK：

```powershell
uv run --locked --no-sync --cache-dir tmp/uv-cache python -m tools.verify_equivalent_solder_ball_floxml
uv run --locked --no-sync --cache-dir tmp/uv-cache ruff check tools/equivalent_solder_ball_probes.py tools/equivalent_solder_ball_rules.py tools/verify_equivalent_solder_ball_floxml.py
```

验证覆盖三类模板、四种配置、普通/矩形/单列、交错、奇偶中央去球、中央阵列、名单/CSV、
直径/间距/高度及两种焊料。不包含 Chip Array 未开放的原生等效分支、任意材料/任意输入穷举，
也没有做温度场等价验证。本任务不对应已有 TASK 文件。
