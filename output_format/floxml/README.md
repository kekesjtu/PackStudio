# FloXML 契约

五份 XSD 原样复制自本机 FloTHERM 2504：
`E:\Program Files\Siemens\SimcenterFlotherm\2504\WinXP\PlugIns\XML_PLUGIN_SCHEMA`。
这些厂商契约文件保留原始内容与长度，不按项目 Python/TS 的 300 行规范拆分。
生产导出器不依赖它们，也不依赖安装目录。

`bare-die.floxml` 是当前 PackageModel 的导出样例，根为 `xml_case`；
ECXML 的 `neutralXML` 是另一种格式。单位为 m、W、kg/m³、J/(kg·K)、W/(m·K)。
材料名为唯一 ID，显示名在 notes，避免同名材料引用歧义。

生产输出是有限厚度物理块和体热源。源几何不含材料，不能计入质量。
未设置目标求解域、默认散热边界、辐射或 PACK collapsed 几何；
当前外部边界/网格值仅记入 notes，不保证导入器应用。

格式检查：`uv run --locked pytest tests/backend/exporters/test_floxml.py`。
已检查 XSD 和逐块保真；实际 FloTHERM 导入后的求解/网格行为仍需下游验证。
