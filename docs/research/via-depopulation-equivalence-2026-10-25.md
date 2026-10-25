# PACK 原生 Via Depopulation 与物性等效

## 1. 结论

WB PBGA 的 Isotropic／Orthotropic Cuboid、FC PBGA Core 的 Orthotropic Cuboid 都保留名义完整阵列的居中包络。显式去孔只按剩余孔数修改孔体积分数，不按剩余孔的实际外缘收缩或移动包络：

$$
L_x=(N_x-1)e_v+d_v,\qquad L_y=(N_y-1)e_v+d_v
$$

$$
\phi_{\rm depop}=\frac{N_{\rm remain}\pi d_v^2}{4L_xL_y}
=\frac{N_{\rm remain}}{N_xN_y}\phi_{\rm full}
$$

后续单孔镀层比例、孔与基体的混合公式保持原有规则。去孔减少 Via 材料份额，同时增加基体份额；不能将空缺位置另计为空气，也不能直接把最终导热率、密度、比热乘以剩余比例。

WB／FC 各向异性模式保持基体平面导热率，只更新轴向导热率；WB 各向同性模式把更新后的轴向导热率复制到所有方向。密度按体积加权，比热按质量加权。

实测同孔数的 16 孔周边框和左上 4×4、4 孔四角和左上 2×2，其等效包络及物性完全相同。等效分支抹平了去孔的空间分布；离散分支仍输出相应位置的剩余孔，单孔材料不变。

## 2. 原生采集

- PACK 2504，flopack.exe 文件版本 2025.13.1.1142。
- 可复核工具：[verify_via_depopulation.py](../../tools/verify_via_depopulation.py)。
- 5 分支：WB Orthotropic、WB Isotropic、WB Discrete、FC Core Orthotropic、FC Core Discrete。
- 每分支 8 方案：默认空名单、显式全 25 孔、去角后 24 孔、周边 16 孔、角落 4×4、四角 4 孔、角落 2×2、单个角孔。
- 合计 40 个直接导出和 40 个保存重载导出，全部通过；各分支模式保持不变，去孔名单、几何及材料保存重载一致。
- 验证数据：flotherm_pack_data/validation/via_depopulation_2026-10-25-confirmed/results.json，包含原生运行记录、脚本／可执行文件／DLL／输出指纹。

通过原生 modify_component 设置 thermalVias／coreVias 的 depopulationDialog；输入是保留孔位名单，而非删除孔位名单。保存 ZIP 的 .var3 成员存储该名单；只检查 .des 文本不足以确认去孔保存成功。

默认空名单表示按完整规则阵列生成，不代表全删。本轮没有建立“零孔”方案。XML 给 depopulationDialog 传空字符串会被原生拒绝；正式验证集直接载入默认空名单基线，运行无原生错误。早期带该错误的探针不作为验收集。

编辑器孔位行号由上往下，FloXML 的 y 坐标由下往上；离散位置校验显式转换，避免把索引方向差异误判为删错孔。

## 3. 对照数值

两者均为 5×5，铜材料为 385 W/(m·K)、8930 kg/m³、385 J/(kg·K)。

- WB：孔径 0.25 mm、镀层 0.025 mm、间距 1.27 mm；包络 5.33×5.33×0.324 mm；基体 BT。
- FC：孔径 0.20 mm、镀层 0.025 mm、间距 0.80 mm；包络 3.40×3.40×1.15 mm；基体 Substrate PBGAFC (Typical)。

| 分支 | 剩余孔数 | 孔体积分数 | $k_z$ | $\rho_{\rm eff}$ | $c_{\rm eff}$ |
| --- | ---: | ---: | ---: | ---: | ---: |
| WB Orthotropic | 25 | 0.04319719 | 6.178491 | 1956.795664 | 882.961029 |
| WB Orthotropic | 24 | 0.04146930 | 5.939351 | 1954.523838 | 884.440142 |
| WB Orthotropic | 16 | 0.02764620 | 4.026234 | 1936.349225 | 896.397994 |
| WB Orthotropic | 4 | 0.00691155 | 1.156559 | 1909.087306 | 914.761669 |
| WB Orthotropic | 1 | 0.00172789 | 0.439140 | 1902.271827 | 919.434829 |
| FC Orthotropic | 25 | 0.06794102 | 15.172051 | 2036.349130 | 851.132675 |
| FC Orthotropic | 24 | 0.06522338 | 14.725169 | 2030.895164 | 853.747245 |
| FC Orthotropic | 16 | 0.04348225 | 11.150113 | 1987.263443 | 875.180443 |
| FC Orthotropic | 4 | 0.01087056 | 5.787528 | 1921.815861 | 909.155014 |
| FC Orthotropic | 1 | 0.00271764 | 4.446882 | 1905.453965 | 918.013326 |

WB 的平面导热率始终为 0.2，FC 为 20。WB Isotropic 的三个导热分量均等于表中 WB 的 $k_z$。上述参数下去孔导致密度降低、比热升高；其他材料需按混合公式判断增减方向。

## 4. 范围与限制

本轮实测为 WB 两层分支、FC 已初始化 Core Vias 的固定 5×5 阵列，不外推四层、其他阵列规模、零孔、FC 微孔区或 Chip Array。

QFN 原生参数目录未见对应 Via Depopulation 编辑器，不把 WB／FC 的去孔规则直接套到 QFN Lumped。Chip Array 与 Solder 的对应关系见独立研究，本轮操作不涉及 Solder。

上述结果说明本机 PACK 的生成及导出规则，不等同于真实去孔后局部温度场的等效精度验证。
