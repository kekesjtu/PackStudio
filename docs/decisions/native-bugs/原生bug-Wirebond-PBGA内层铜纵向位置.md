# Wirebond PBGA 内层铜纵向位置

Metal Layers 的 Depth 是基板顶面到该层顶面的距离。设 $z_s$ 为基板顶面，$Z_n$、$t_n$ 为该层的 Depth 与 Thickness：

$$
z_{\max,n}=z_s-Z_n,\qquad z_{\min,n}=z_s-Z_n-t_n
$$

内层铜与对应 Disconnect to Via 介质块共用该纵向范围。厚度增加时从固定层顶向下延伸，Depth 增加时整层向下平移。层深非负、厚度为正，两者之和不得超过基板总厚度。断开区以基板介质块表达，重叠按[重叠块规则](../modeling/重叠块与警告.md)处理。

PACK 原生内层铜底面使用 $z_s-Z_n-2t_{\rm top}$，因此铜厚与两倍顶铜厚度不同时，内层铜与断开区错位。对照样本位于 `flotherm_pack_data/packages/pbga_wb/cases/metal_depth_*/`。
