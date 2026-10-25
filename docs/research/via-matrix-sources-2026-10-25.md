# Via 阵列等效基体的来源核查

## 结论

- WB：从 Package Substrate → Dielectric Material 当前选材继承；
  原生属性 packageSubstrate.dielectricMaterial，DES 键 k_substr，默认内置 BT。
- FC PBGA Core：同一组件／属性／DES 键，默认内置 Substrate PBGAFC (Typical)，
  使用该各向异性材料的方向参数。FR4 (25% Fibre) 的替代对照确认方向分量跟随选材。
- QFN Lumped：未见 k_substr 或独立基体选材项。反算 0.32/1200/880，
  不随本轮塑封料与芯片胶替代变化；疑似内部 FR4 类板材背景，库项身份未确认。
- FC 改用各向同性 BT 时出现方向导热贡献归零的原生异常。
  不将各向异性材料下的成功继承外推为任意选材都正常。

## 证据

PACK 2504 文件版本 2025.13.1.1142。
WB 为 PBGA_121_15X15mm 的 orthotropicCuboid，
FC 为 PBGAFC_49_6X6mm 的已启用 Core Vias／orthotropicCuboid，
QFN 为 QFN_12X12_100 的 lumped。
三类均保持本地已归档的单孔、间距和阵列参数。

8 个首次方案及其保存 DES 原生重载，共 16 份正式 FloXML。
4 个正式原生批次退出码均为 0，日志没有 ERROR。
方向导热率、密度、比热均独立由阵列输出反算，并与相应选材对照。
换材通过原生 DES 的材料名称键应用，并从原生保存 DES 及实际几何材料回读。

| 对照 | 基板选材／所改材料 | 反算 kx、ky、kz | 反算 rho、cp |
| --- | --- | --- | --- |
| WB 默认 | BT | 0.2、0.2、0.2 | 1900、921 |
| WB 换材 | FR4 | 0.3、0.3、0.3 | 1200、880 |
| FC 默认 | Substrate PBGAFC (Typical) | 20、20、4 | 1900、921 |
| FC 换各向异性材料 | FR4 (25% Fibre) | 0.5、0.5、0.3 | 1200、880 |
| FC 换各向同性材料 | BT | 0、0、约0 | 1900、921 |
| QFN 默认 | EME-7730LF／DieAttach-2600BT | 0.32、0.32、0.32 | 1200、880 |
| QFN 换塑封料 | Epoxy Overmold (Typical) | 0.32、0.32、0.32 | 1200、880 |
| QFN 换芯片胶 | QMI 595 | 0.32、0.32、0.32 | 1200、880 |

## QFN 反算与材料判断

令 phi 为孔阵列的外径面积填充率，单孔材料按空心铜镀层计算。
从等效材料反算：

$$
\rho_b=\frac{\rho_{\rm eff}-\phi\rho_v}{1-\phi}
$$

$$
c_b=\frac{\rho_{\rm eff}c_{\rm eff}-\phi\rho_vc_v}{(1-\phi)\rho_b}
$$

$$
k_{b,z}=\frac{k_{{\rm eff},z}-\phi k_v}{1-\phi},\qquad
k_{b,x}=k_{{\rm eff},x},\quad k_{b,y}=k_{{\rm eff},y}
$$

核对本机已提取的 131 个内置材料条目，没有找到
(0.32,0.32,0.32,1200,880) 的完整匹配项。
与 QFN 的密度和比热同时相同的条目为：

- FR4：k=0.3，各向同性。
- FR4 (25% Fibre)、FR4 (30% Fibre)：kx=ky=0.5、kz=0.3。

因此“FR4 类内部背景参数”是依据数值和板侧位置的猜测。
不能证明它当前调用了具名 FR4 库项，也未证明它一定是硬编码常数或某旧版参数。
FC 的典型基板库项可能概括有机基材与布线影响，同样不能从 20/4 唯一反推具体组成。

## FC 各向同性替代异常

BT 的内置物性为 k=0.2、rho=1900、cp=921，原生几何中基板也引用了该材料。
但 Core Via 阵列输出的 kx、ky 为 0，轴向中可反算的基体贡献也约为 0，
只有 rho/cp 正常匹配。保存重载不改变此结果。

这与该库项非当前类型方向存储 kx/ky/kz 为 0 的情况相符，
但未经厂商源码确认，不把此相符关系作为内部 getter 调用的证明。
该异常单独保留，不以“继承基板材料”掩盖其数值限制。

## 文件与复现

原始数据仅保存在本地：
flotherm_pack_data/validation/via_matrix_sources_2026-10-25/。
baselines/ 三个默认分支，variants/ 四个替代方案，anisotropic/ 补充一个各向异性方案，
reload-confirmed/ 八个正式重载；未执行的 reload/ 准备目录不计入正式结果。

机器可读记录见 [results.json](../validation/via-matrix-sources/results.json)。
其中包含材料库条目和原生脚本、XML、DES、软件版本的指纹。

离线核查：

~~~powershell
uv run --locked python -m tools.verify_via_matrix_sources
~~~

重新采集需选择不存在的新目录：

~~~powershell
$packInstallation = 'E:\Program Files\Siemens\SimcenterFlotherm\2504'
$matrixOutput = 'flotherm_pack_data/validation/via_matrix_sources-new-run'
foreach ($matrixPhase in @('baselines','variants','anisotropic','reload-confirmed')) {
    uv run --locked python -m tools.verify_via_matrix_sources --prepare $matrixPhase --installation $packInstallation --output $matrixOutput
    & ./tools/replay_wb_via_stack.ps1 -Installation $packInstallation -Directory "$matrixOutput/$matrixPhase"
}
uv run --locked python -m tools.verify_via_matrix_sources --output $matrixOutput
~~~

本次只修改用户指定笔记的基体来源章节；保留其他章节和用户编辑。
未修改生产模板、安装材料库或输出契约；未验证下游数值求解。
