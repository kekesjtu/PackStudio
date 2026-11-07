# FC Slug 支脚与胶层纵向位置

FC CBGA/PBGA 的塑封顶部启用 Slug 时，支脚以基板顶面为基准。支脚底面比基板顶面高一个支脚净空，支脚厚度取 Slug 板厚。启用粘接层时，其底面贴合基板，顶面贴合支脚底面，厚度等于净空。关闭粘接层时保留支脚净空。原生样本中支脚与胶层额外抬升了一个凸点高度。

竖壁底面与支脚底面齐平，顶面贴合水平板底面。顶部中央板顶面与塑封体顶面齐平，水平板底面位于塑封体顶面以下一个板厚加一个顶部台阶高度。

固定塑封厚度时，Slug 顶部随塑封顶面定位。塑封体与芯片齐平时，塑封顶面等于基板顶面加凸点高度和芯片厚度，Slug 顶部及竖壁顶端随之移动。两种情况下支脚与胶层均以基板顶面定位。Wirebond PBGA 以阻焊层顶面定位支脚与胶层。

原生样本见 [FC CBGA](../../../flotherm_pack_data/packages/cbga_fc/options/encapsulant_with_slug/drop_in_slug/adhesive_present_under_slug_foot/true/model.xml)与 [FC PBGA](../../../flotherm_pack_data/packages/pbga_fc/options/encapsulant_with_slug/drop_in_slug/adhesive_present_under_slug_foot/true/model.xml)。
