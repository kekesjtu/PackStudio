# 输出格式

桌面端在“导出 XML”中选择格式。CLI 的 `generate` 根据输出文件名识别 `.pta.xml`。

| 文件 | 用途 |
| --- | --- |
| [PackStudio XML](packstudio/README.md)（`.packstudio.xml`） | 下游网格与求解模块的模型接口，按米描述几何，按瓦描述块功率。 |
| [PTA 工程示例](pta/bare-die.pta.xml)（`.pta.xml`） | PTA 3.1.0 / 3.2.1 工程格式，使用根级独立块、矩形阵列和布尔差集，几何单位为毫米，体积功率密度为 W/m³。 |

仓库内由 PackStudio 导出的 PTA 样例统一放在 `pta/`，包括[带焊球和通孔的 BGA](pta/BGA-焊球与通孔.pta.xml)。外部[格式说明与原始样例](PTA-工程文件/工程文件格式说明.md)保存在 `PTA-工程文件/`。

PTA 工程采用三维稳态固体传热、FDM 和 300 K 环境温度与初始温度。材料保留标量、三向或温度相关导热率。边界条件由使用者在 PTA 中设置，网格线与求解结果由 PTA 生成。

[floxml/](floxml/README.md)中的厂商 XSD 和示例只供原生 PACK 研究工具使用，不随产品分发。
