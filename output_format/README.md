# 输出格式

PackStudio 当前只输出 FloXML。正式格式契约、五份厂商 XSD 与 Bare Die 示例均在
[floxml/](floxml/README.md)。

```text
output_format/
├── README.md
└── floxml/
    ├── README.md
    ├── bare-die.floxml
    └── *.xsd
```

停止使用的格式规范、样例及历史说明已保存到
[参考资料归档](../archive/README.md)，不参与当前生产导出和格式校验。
输出范围决策见 [ADR-0031](../docs/decisions/0031-仅保留FloXML输出.md)。
