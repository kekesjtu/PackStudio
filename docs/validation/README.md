# 验证数据与测试夹具

本目录提供回归测试输入、原生导出证据、模型比较数据与预设审计报告。
证据文件中的输入、版本、来源路径和哈希共同标识对应的验证数据。
项目功能范围见[决策索引](../decisions/README.md)。

## 回归输入与审计

| 数据 | 用途 |
| --- | --- |
| `floxml/evidence.zip` | 为原生比较和引线框回归测试提供 FloXML 证据 |
| `floxml/results.json` | 记录对应证据批次的模型比较结果与分类 |
| `floxml-model-fixes/results.json` | 提供专项模型比较数据 |
| `catalog_presets.json` | 记录 342 个源预设的输入哈希、几何引用与 FloXML XSD 审计 |
| [target-pack-fidelity](target-pack-fidelity/README.md) | Bare Die、两个 FC 与 Chip Array 的 93 组原生证据及建模规则 |

`tests/backend/test_floxml_comparison.py` 与
`tests/backend/templates/test_leadframe_model_fixes.py` 读取原生导出证据；
`tests/backend/templates/test_source_presets.py` 检查预设审计的覆盖范围和输入指纹。
其余原生实验 JSON 与证据压缩包按各自数据用途维护。

## 验证入口

```powershell
uv run --locked pytest
uv run --locked python -m tools.validate_catalog_presets
```

预设审计工具生成模型、验证 FloXML 并写入 `catalog_presets.json`。
原生比较模块位于 `tools/floxml_validation/`，材料、目录和参数辅助模块位于
`tools/pack_reference/`。本机原生导出操作见 [FloSCRIPT 说明](../../FLOSCRIPT.md)。
