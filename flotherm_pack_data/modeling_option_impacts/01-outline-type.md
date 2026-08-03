# Outline Type

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `new_package.outlineType` |
| 值 | `standardOutline` / `nonStandardOutline` |
| 模板 | 除 Bare Die 外的 7 类模板 |
| 默认 | `standardOutline` |
| 证据 | 已验证；Non-Standard 存在数据边界 |

## 建模影响

`Standard Outline` 显示封装子类型和 JEDEC Footprint，由预设表初始化后续尺寸、数量、
材料和建模默认值。`Non-Standard Outline` 隐藏 JEDEC 选择，应由用户输入的完整参数驱动
同一套模板生成器。它本身不是一个应当删减物理实体的开关。

现有单变量脚本只把 `outlineType` 改为 `nonStandardOutline`，没有继续写入自定义尺寸。
七类输出均出现：

- `<materials/>`、`<sources/>`、`<geometry/>` 为空；
- 网格最大尺寸为 `-inf` 或 `-8.9884656743115788e+306`；
- 标准预设产生的全部材料和实体被移除。

这表示 PACK 停留在“尚未初始化的自定义封装”状态，不是有效 Non-Standard 物理模型。

## PackStudio 生成规则

```text
if outline_type == standard:
    resolved_parameters = preset_table[jedec_id]
else:
    resolved_parameters = validate(user_parameters)

model = common_template_generator(resolved_parameters)
```

当最终参数完全相同，`outline_type` 不应在几何层引入额外差异。PackStudio 不应复制
当前空 FloXML 或哨兵网格值。

## 证据

- `../templates/qfp_family/ui.json`
- `../templates/qfp_family/xml_variations/option_switches/opt_v2_c001_outlinetype_nonstandardoutline/`
- `../templates/soic_family/validation/nonstandard_outline_baseline_model.xml`
- `../templates/soic_family/validation/nonstandard_outline_length_d_5_model.xml`
