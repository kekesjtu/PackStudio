# 原生bug：SOP 芯片与胶层堆叠

## 决策

PackStudio 将 SOP 的 `die` 与 `die_attach` 从同一底面开始的行为认定为 PACK 原生 bug。
SOP 按承载台、芯片胶、芯片的顺序建立连续堆叠。

## 建模规则

适用模板为 `sop`。承载台顶面使用承载台实际底面与实际厚度计算。
设 $t_{da}$ 为芯片胶厚度，$t_d$ 为芯片厚度：

$$
z_{\rm flag,top}=z_{\rm flag,bottom}+t_f
$$

$$
z_{\rm attach,bottom}=z_{\rm flag,top},\qquad
z_{\rm attach,top}=z_{\rm flag,top}+t_{da}
$$

$$
z_{\rm die,bottom}=z_{\rm attach,top},\qquad
z_{\rm die,top}=z_{\rm die,bottom}+t_d
$$

键合线几何使用实际端点高差：

$$
H=z_{\rm die,top}-z_{\rm lead,top}
$$

在承载台底面相对引线框底面下沉 $d_f$ 的定义下：

$$
H=t_d+t_{da}+t_f-t_l-d_f
$$

当承载台厚度 $t_f$ 与引线厚度 $t_l$ 相等时，该式简化为 $H=t_d+t_{da}-d_f$。
水平段高度、竖直段高度和折弯方向共用实际端点高差。
塑封体容纳校验使用堆叠后的实际芯片顶面。
芯片尺寸和总体功率分别由芯片参数和热源参数决定。

## 依据与范围

依据为用户确认的原生 bug 处理范围，以及
[SOP Bond Wires 第 1 节](../../../Flotherm_PACK_Research/packages/07_SOP/Bond_Wires.md#1-参数怎样决定几何)
中芯片、胶层同底面与胶厚变化实验。

本决策定义 SOP 芯片、胶层及承载台的接触关系，并为键合线提供端点坐标。
其他组件的重叠表达遵循[重叠块与警告](重叠块与警告.md)。
本项几何以堆叠和接触关系作为验收依据，原生 FloXML 样本作为原生行为证据保存。

## 实现对照

`src/packstudio/templates/package_library/leadframe/sop.py` 的 `_build`
使用 `flag_z + lead_thickness` 作为 `die_z`，芯片与胶层同时使用该起点。
该计算与本决策的承载台实际顶面、胶层和芯片连续堆叠存在实现差距。
键合线生成使用 `die_top` 与 `lead_top`，其端点随堆叠坐标联动。

## 验收标准

- 胶层底面贴合承载台顶面，胶层顶面贴合芯片底面，芯片与胶层共面接触。
- 胶厚增加 $\Delta t$ 时，芯片上下表面均上移 $\Delta t$，芯片厚度与总体功率保持原值。
- 承载台厚度与引线厚度分别取不同值时，胶层底面仍贴合承载台实际顶面。
- $H$ 的正、负和零值对应一致的键合线端点、竖直高度与折弯方向。
- 塑封体容纳校验覆盖芯片抬高后的实际范围。
