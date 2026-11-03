# 原生bug：FC Slug 支脚与胶层纵向位置

## 决策

PackStudio 将 FC CBGA、FC PBGA 中 Slug 支脚及粘接层额外抬高一个 bumps 高度的行为认定为 PACK 原生 bug。
粘接层底面贴合基板顶面，顶面贴合 Slug 支脚底面。

## 建模规则

适用模板为 `cbga_fc`、`pbga_fc`，顶部结构为 Encapsulant 且启用 Slug。
设 $S$ 为基板顶面，$g$ 为支脚净空，$t$ 为 Slug 板厚，$G$ 为 Slug 偏移，$T$ 为塑封体顶面：

$$
z_{\rm foot,bottom}=S+g,\qquad z_{\rm foot,top}=S+g+t
$$

启用支脚粘接层时：

$$
z_{\rm adhesive,bottom}=S,\qquad z_{\rm adhesive,top}=S+g
$$

粘接层厚度为 $g$；关闭粘接层时，支脚仍保留相同净空。
竖壁底面与支脚底面共面，顶面接至水平板底面：

$$
z_{\rm wall,bottom}=S+g,\qquad z_{\rm wall,top}=T-t-G
$$

Slug 顶部中央板顶面为 $T$，水平板底面为 $T-t-G$。
各板件厚度和横向尺寸由各自参数决定。
固定塑封厚度时，bumps 高度不参与 Slug 定位；塑封体与芯片齐平时，$T=S+t_{\rm bumps}+t_{\rm die}$，顶部及竖壁顶端随芯片顶面变化，支脚和胶层仍以基板顶面定位。

Wirebond PBGA 的支脚和胶层以阻焊层顶面为基准，保留阻焊层厚度偏移。

## 依据与范围

依据为用户确认的原生 bug 处理范围，以及原生 FloXML 样本：

- [FC CBGA：支脚粘接层开启](../../flotherm_pack_data/template/cbga_fc/opt_v2_c009_adhesivepresentunderslugfoot_true/model.xml)
- [FC PBGA：支脚粘接层开启](../../flotherm_pack_data/template/pbga_fc/opt_v2_c011_adhesivepresentunderslugfoot_true/model.xml)

两例基板顶面均为 1.55 mm，bumps 高度为 0.10 mm，支脚净空为 0.10 mm。
原生胶层范围为 1.65～1.75 mm，支脚底面为 1.75 mm；胶层顶面接触支脚，底面与基板之间存在 0.10 mm 的额外间隙。
本决策对应胶层范围为 1.55～1.65 mm，支脚底面为 1.65 mm。

本项以几何接触关系作为验收依据，原生 FloXML 样本作为原生行为证据保存。

## 验收标准

- 两类 FC 封装四侧胶层底面均贴合基板顶面，顶面均贴合对应支脚底面。
- 胶层开关不改变支脚净空；改变净空时，胶层厚度和支脚底面同步变化。
- 改变 bumps 高度不改变支脚和胶层的纵向位置；固定塑封厚度与芯片齐平模式分别遵循各自顶部定位规则。
- 竖壁底面接至支脚底面，顶面接至水平板底面；Slug 板厚保持参数值。
- FloXML 导出的胶层、支脚与竖壁保持上述接触关系。
- Wirebond PBGA 胶层底面仍位于阻焊层顶面。
