# 原生bug：Wirebond PBGA 内层铜纵向位置

## 决策

PackStudio 将 Wirebond PBGA 内层铜使用两倍顶铜厚度定位底面的行为认定为 PACK 原生 bug。
Metal Layers 的 Depth 表示基板顶面到该层顶面的距离，各层厚度从该顶面向下展开。
内层铜与对应 Disconnect to Via 介质块共用相同的纵向范围。

## 建模规则

适用模板为 `pbga_wb`，覆盖金属层表中的全部内层。
设 $A_1$ 为基板底面高度，$A_2$ 为基板总厚度，$Z_n$、$t_n$ 为该层的 Depth、Thickness：

$$
z_s=A_1+A_2,\qquad
z_{\max,n}=z_s-Z_n,\qquad
z_{\min,n}=z_s-Z_n-t_n
$$

内层铜和对应断开区的顶、底面均使用以上坐标，厚度均为 $t_n$。
固定基板顶面和该层表格参数时，内层位置与顶铜厚度无关。
Depth 固定时，该层顶面固定，厚度增加量向下延伸。
Thickness 固定时，Depth 增加量使整层沿负 Z 方向等量平移。
各层要求 $Z_n\geq0$、$t_n>0$、$Z_n+t_n\leq A_2$。

金属层的平面尺寸、覆盖率等效物性和断开区平面范围分别遵循各自规则。
断开区以基板介质矩形块表达；金属层、通孔与断开区按
[重叠块与警告](重叠块与警告.md)参与模型、预览和导出。
通孔上下端点由[通孔纵向位置决策](原生bug-Wirebond-PBGA通孔纵向位置.md)定义。

## 依据与范围

依据为用户确认的修复范围，以及
[研究笔记 Metal Layers 第 3 节](../../../Flotherm_PACK_Research/packages/08_Wirebond_PBGA/Metal_Layers.md#3-断开区的纵向位置)
记录的原生几何和六组独立变参实验。

PACK 2025.13.1.1142 的原生内层铜底面为 $z_s-Z_n-2t_{\rm top}$，
顶面为该底面加 $t_n$；原生断开区使用 $[z_s-Z_n-t_n,z_s-Z_n]$。
两者底面偏差为 $2t_{\rm top}-t_n$，在 $t_n=2t_{\rm top}$ 时重合。

以 $z_s=1.16$、$Z_n=0.20$、$t_n=0.036$、$t_{\rm top}=0.010$ 为例，单位均为 mm：
原生铜层为 $0.940\sim0.976$，断开区为 $0.924\sim0.960$；
本决策规定两者均为 $0.924\sim0.960$。

`docs/validation/wb-metal-depth/evidence.zip` 保存六组原生输入、DES 回读、
FloSCRIPT、FloXML、版本、哈希和 XSD 检查结果。
源证据保留原生坐标；本项按 Depth 定义和铜层与断开区对齐关系验收。


## 验收标准

- 上述实例中，内层铜和断开区的范围均为 $0.924\sim0.960$ mm。
- 固定基板顶面、Depth 和该层厚度时，改变顶铜厚度保持该内层位置。
- 固定 Depth 时，改变该层厚度保持顶面，底面随厚度变化。
- 改变 Depth 时，该层及其断开区等量平移。
- 每个勾选 Disconnect to Via 的内层，铜层和断开区的上下表面均对齐。
- 离散、正交及各向同性通孔表达使用相同的内层铜定位规则。
- 默认 $t_n=2t_{\rm top}$ 案例符合相同公式，FloXML 坐标与生成模型一致。
