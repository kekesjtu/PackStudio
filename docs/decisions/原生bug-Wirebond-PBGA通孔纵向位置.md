# 原生bug：Wirebond PBGA 通孔纵向位置

## 决策

PackStudio 将 Wirebond PBGA 通孔起点使用顶铜厚、在不等铜厚下整体偏移的行为认定为 PACK 原生 bug。
Thermal Vias 的上下端面分别贴合底铜层顶面和顶铜层底面。

## 建模规则

适用模板为 `pbga_wb`，覆盖两层和四层基板。
设 $A_1$ 为基板底面高度，$A_2$ 为基板总厚度，$t_{\rm bottom},t_{\rm top}$ 为底、顶铜厚：

$$
z_{\min}=A_1+t_{\rm bottom},\qquad
z_{\max}=A_1+A_2-t_{\rm top}
$$

$$
h_v=z_{\max}-z_{\min}=A_2-t_{\rm bottom}-t_{\rm top}
$$

通孔端点以生成后的外层铜层内表面为统一来源，高度由两端相减得到。
离散孔和采用通孔包络的等效表达共用同一组纵向端点。
通孔阵列、等面积截面、去孔配置与材料计算分别遵循各自规则。
参数校验要求 $h_v>0$。

## 依据与范围

依据为用户确认的原生 bug 处理范围，以及
[Vias Discrete 第 3 节](../../../Flotherm_PACK_Research/packages/common/Vias/Vias_Discrete.md#3-三类封装的纵向位置)
中两层、四层不等铜厚对照。

记录中 $A_1=0.6$、$A_2=0.36$、$t_{\rm top}=0.01$、$t_{\rm bottom}=0.04$，单位均为 mm。
PACK 原生通孔范围为 $0.61\sim0.92$ mm；
本决策对应范围为 $0.64\sim0.95$ mm，高度为 $0.31$ mm。

本项纵向位置以铜层接触关系作为验收依据，原生 FloXML 样本作为原生行为证据保存。

## 实现对照

`src/packstudio/templates/package_library/bga/pbga_wb.py` 的 `_build`
使用 `bga_height + top_trace` 作为通孔起点，孔高为 `substrate - top_trace - bottom_trace`。
该起点与本决策的底铜层顶面存在实现差距。

## 验收标准

- 上述不等铜厚案例的通孔范围为 $0.64\sim0.95$ mm。
- 两层、四层基板中，每个保留孔的上下端面均贴合对应外层铜层内表面。
- 顶、底铜厚相等时，端点符合相同公式。
- 显式去孔影响保留孔集合，所有保留孔共用同一纵向范围。
- 采用等效表达时，包络块共用离散孔的纵向范围。
