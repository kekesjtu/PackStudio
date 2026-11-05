# FloXML 契约

## 文件与单位

输出根节点为 `xml_case`，通过 `assembly` 维护组件层级，`cuboid` 表达物理矩形块。
示例为 [bare-die.floxml](bare-die.floxml)。

| 物理量 | 输出单位 |
| --- | --- |
| 位置、尺寸 | m；内部 mm 在导出时换算 |
| 功率 | W |
| 密度 | kg/m³ |
| 比热 | J/(kg·K) |
| 导热率 | W/(m·K) |

材料以唯一 ID 引用，显示名称保存在 notes；支持常量各向同性、正交各向异性及
带系数和参考温度的温度相关材料。No Attachment 对应的实体保留几何，材料引用留空。
几何、材料、物性和功率从生成模型直接映射。

## 导出行为

导出器输出模型中的有限厚度物理块，保留组件父子关系。
同一块的多个功率项累加；物理块承担材料与质量，热源几何承担功率分配。
芯片功率使用体热源表达。

Bare Die、Flip Chip CBGA/PBGA、Chip Array 保留原生矩形块及重叠关系，
重叠检测结果以 warning 返回并写入 notes。局部网格约束、非物理网格区域、
结温与壳温监测点随模型输出。

依据[固体传热范围决策](../../docs/decisions/仅支持固体传热与辐射属性留空.md)，
`attributes` 中固定输出 `<surfaces/>` 和 `<radiations/>`，不输出表面辐射属性定义、
发射率数值或几何对象上的相关属性引用。

目标求解域、边界条件和实际网格划分由下游软件设置。
模型中的边界信息和元数据以 notes 保存，作为描述性追溯信息。

## XSD 与验证

五份 XSD 来自本机 FloTHERM 2504 的 `XML_PLUGIN_SCHEMA` 目录，
文件保持厂商原始内容与结构，用于开发期格式校验。

```powershell
uv run --locked pytest tests/backend/exporters/test_floxml.py
```

测试检查 XSD、块坐标和尺寸、层级、材料绑定、物性与功率。
实际 FloTHERM 导入、网格划分和求解分别通过目标软件验收。
