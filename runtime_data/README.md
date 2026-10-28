# 运行数据、预设与材料库

生产运行从本目录读取版本化 JSON，运行库随应用分发。

## 数据组织

| 路径 | 内容 |
| --- | --- |
| `presets/<family>/<原始名称>.json` | 342 个原生预设、参数状态、向导分支及原始 DES 字段 |
| `presets/index.json` | 预设路径、分支与来源哈希 |
| `materials/<分类>/<文件>.json` | PACK 内置材料记录 |
| `materials/index.json` | 材料名称、分类、路径和哈希 |
| `materials/runtime.json` | 运行材料 ID、颜色与项目补充材料 |
| `pack_bindings.json` | 运行字段和材料组件到原生数据的路径映射 |
| `templates/<模板 ID>.json` | 向导字段、范围、条件、建模选项、Bare Die 基线设置与审核物性 |

八类模板 ID 为 `chip_array`、`bare_die`、`cbga_fc`、`pbga_fc`、`pqfp`、`qfn`、
`sop`、`pbga_wb`。原始来源的 QFN、tsop_conv 等目录名保留用于追溯。
Bare Die 使用模板中的基线设置，芯片尺寸等参数支持逐项编辑。

## 读取与覆盖

读取预设后，通过绑定表投影当前支持的字段和材料，再应用当前方案的修改。
七类封装的参数取自所选预设的原生记录，Bare Die 的参数取自模板基线设置。
原生空值在界面显示为空白。
分支按启用状态参与模型生成，启用后缺少必需参数时提示填写。
原生记录用于来源追溯，运行绑定表定义可编辑的字段与材料组件。

材料选择参与组分等效计算，显式等效材料物性覆盖具有最终优先级。
温度依赖材料的基准导热率、系数与参考温度进入模型及 FloXML；组分混合使用参考值。
Bumps 物性使用有厚度的各向同性等效算法，建模约定见
[BGA 与 Bumps 建模表达](../docs/decisions/BGA与Bumps建模表达.md)。

材料选项中的 `*` 展开为运行材料库；空字符串表示 No Attachment。
组件选材按材料库分类组织“材料组 + 组内材料”，原生缺省材料的默认值见
[材料组与默认材料](../docs/decisions/材料组与默认材料.md)。
金属层表以 Depth、Thickness、Coverage 保存，运行输入长度单位为 mm、覆盖率单位为 %。
Chip Array 与 Wirebond PBGA 的两层/四层选择初始化层表，表格编辑与外层铜厚输入联动。
Wirebond PBGA 的层表包含逐层 Disconnect to Via 开关。
Bare Die、两个 FC 和 Chip Array 的建模与证据见
[原生对照](../docs/validation/target-pack-fidelity/README.md)。
PQFP、QFN、SOP 与 Wirebond PBGA 的建模规则和全预设对照见
[四类线焊封装原生对照](../docs/validation/remaining-pack-fidelity/README.md)。

封装参数初值在原生预设或 Bare Die 基线设置中维护，用户输入覆盖方案中的对应值。
参数来源与空值处理见[预设参数规则](../docs/decisions/预设参数来源与空值规则.md)。
分发方式见[运行数据决策](../docs/decisions/JSON运行参数与参考数据解耦.md)。

## 提取与验证

原生提取依赖本机安装及经过审核的二进制布局；切换版本需要重新核验。

```powershell
uv run --locked python -m tools.pack_reference "E:/Program Files/Siemens/SimcenterFlotherm/2504"
uv run --locked python -m tools.validate_catalog_presets
```

[预设审计](../docs/validation/catalog_presets.json)记录来源、输入哈希、生成检查与 FloXML 校验。
审计覆盖报告列出的生成与格式检查，原生模型的几何和物性通过逐项对照验证。

离线回归直接检查本目录中的 342 个预设、416 个分支、材料引用和索引哈希。
原始 DES 字段与来源哈希的独立比对可设置 `PACK_NATIVE_INSTALLATION` 后运行：

```powershell
$env:PACK_NATIVE_INSTALLATION = 'E:\Program Files\Siemens\SimcenterFlotherm\2504'
uv run --locked pytest tests/backend/test_preset_catalog.py::test_source_provenance_matches_installed_des_files
```

该检查直接读取安装目录中的原始 DES，比对原生字段与来源哈希。
