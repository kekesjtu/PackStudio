# FloXML 输出

## 决策

界面、下载 API、导出器、示例、格式契约与维护工具统一使用 FloXML。
导出器将生成模型中的几何、材料、热源与组件层级映射为 FloXML。

## 契约与验证

- [FloXML 契约](../../output_format/floxml/README.md)维护字段、单位与导出行为。
- 厂商 XSD 和示例位于 `output_format/floxml/`。
- 导出测试检查 XML 结构、单位换算、几何、材料绑定与功率。
- 原生导出证据与模型比较数据位于 `docs/validation/`，用作回归输入。
