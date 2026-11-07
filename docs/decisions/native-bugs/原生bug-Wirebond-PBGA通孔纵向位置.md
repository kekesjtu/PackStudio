# Wirebond PBGA 通孔纵向位置

两层和四层基板中，离散通孔和等效通孔包络的下端贴合底铜顶面，上端贴合顶铜底面。设 $A_1$ 为基板底面高度，$A_2$ 为基板总厚度，$t_{\rm bottom}$、$t_{\rm top}$ 为底、顶铜厚：

$$
z_{\min}=A_1+t_{\rm bottom},\qquad z_{\max}=A_1+A_2-t_{\rm top}
$$

通孔高度为 $z_{\max}-z_{\min}$，要求大于零。去孔改变保留孔集合，保留孔共用上述端点。

PACK 原生通孔下端使用顶铜厚度，不等铜厚时会使通孔整体偏移。原生对照样本见 [两层基板](../../../flotherm_pack_data/packages/pbga_wb/cases/unequal_2_layer/model.xml)与 [四层基板](../../../flotherm_pack_data/packages/pbga_wb/cases/unequal_4_layer/model.xml)。
