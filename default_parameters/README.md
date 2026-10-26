# 默认参数、预设与材料库

生产运行从本目录读取 JSON，不依赖 PACK 安装、DLL 或原始导出文件。

## 数据组织

| 路径 | 内容 |
| --- | --- |
| `presets/<family>/<原始名称>.json` | 342 个原生预设、参数状态、未选分支及原始 DES 字段 |
| `presets/index.json` | 预设路径、分支与来源哈希 |
| `materials/<分类>/<文件>.json` | PACK 内置材料记录 |
| `materials/index.json` | 材料名称、分类、路径和哈希 |
| `materials/runtime.json` | 运行材料 ID、颜色与项目补充材料 |
| `pack_bindings.json` | 已实现字段和材料组件到原生数据的路径映射 |
| `templates/<模板 ID>.json` | 向导字段、范围、条件、默认规格与审核物性 |
| `request.json` | 当前方案的项目初始设置 |

八类模板 ID 为 `chip_array`、`bare_die`、`cbga_fc`、`pbga_fc`、`pqfp`、`qfn`、
`sop`、`pbga_wb`。原始来源的 QFN、tsop_conv 等目录名保留用于追溯。
Bare Die 另有四个项目尺寸预设。

## 读取与覆盖

读取预设后，通过绑定表投影当前支持的字段和材料，再应用当前方案的修改。
有效默认值、禁用分支的编辑初值与不适用状态分别保存，不推测缺失物性。
完整原生记录不代表所有结构和编辑入口均已实现；实现缺口不自动成为功能取舍。

材料选择参与组分等效计算，显式等效材料物性覆盖具有最终优先级。
温度依赖材料的原始系数与参考温度留在库中；当前常量模型使用参考温度值并记录来源。
当前 bumps 的物性算法仍待按 [ADR-0029](../docs/decisions/0029-BGA与Bumps建模表达.md)对齐。

默认值只在运行数据中维护，不在生成器添加重复数值或静默回退。
分发方式见[运行数据决策](../docs/decisions/0016-JSON运行参数与参考数据解耦.md)。

## 提取与验证

原生提取依赖本机安装及经过审核的二进制布局；切换版本需要重新核验。

```powershell
uv run --locked python -m tools.extract_pack_catalog "E:/Program Files/Siemens/SimcenterFlotherm/2504"
uv run --locked python -m tools.validate_catalog_presets
```

[预设审计](../docs/validation/catalog_presets.json)记录来源、输入哈希、生成检查与 FloXML 校验。
审计数据不进入运行包，不替代原生模型的逐项对照验证。
