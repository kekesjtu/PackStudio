# Localize Grid

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `modelingOptions.localizeGrid` |
| 值 | `true` / `false` |
| 模板 | 全部 8 类模板 |
| 默认 | `true` |

## FloXML 影响

8 个单变量案例都只有同一处语义差异：

```xml
<localized_grid>true</localized_grid>
```

变为：

```xml
<localized_grid>false</localized_grid>
```

以下内容完全不变：

- 所有 geometry、source、monitor 和 material；
- `keypoint`、`keypoint_z` grid constraint；
- minimum cell size、maximum size 与 inflation 参数；
- region/top/bottom 边界。

因此它是下游网格器的作用域/网格策略标志，不是封装几何选项。最终网格数量和边界外的
传播方式取决于导入该 FloXML 的 FloTHERM 工程，无法只从 package FloXML 给出固定倍数或
单元数公式。

## PackStudio 实现

模型生成器应原样序列化该布尔值，不应在切换时重算材料或 keypoint 参数。若 PackStudio
分发格式不负责网格设置，可把它归入求解/网格 metadata，而不是热模型实体 schema。

## 证据

- `../templates/bare_die/xml_variations/option_switches/opt_v2_c003_localizegrid_false/`
- `../templates/fbga_fsbga/xml_variations/option_switches/opt_v2_c007_localizegrid_false/`
- `../templates/flip_chip_cbga/xml_variations/option_switches/opt_v2_c010_localizegrid_false/`
- `../templates/flip_chip_pbga/xml_variations/option_switches/opt_v2_c009_localizegrid_false/`
- `../templates/qfn/xml_variations/option_switches/opt_v2_c002_localizegrid_false/`
- `../templates/qfp_family/xml_variations/option_switches/opt_v2_c004_localizegrid_false/`
- `../templates/soic_family/xml_variations/option_switches/opt_v2_c004_localizegrid_false/`
- `../templates/wirebond_pbga/xml_variations/option_switches/opt_v2_c009_localizegrid_false/`
