# PackStudio XML 输出

PackStudio 使用自定义 `.packstudio.xml` 作为下游模型接口，输出轴对齐长方体块、自足的实际材料物性和按块关联的体热源。输出保留导热类型、温度依赖物性与块的重叠关系。一个模型组使用多种材料时，按材料分组。

网格划分、边界条件与求解由下游设置。内部网格参数留在方案和建模核心，辐射属性、非物理区域、监视点与来源记录留在输出范围之外。原生 FloXML 用于研究对照。

字段、单位、数值精度和示例见[PackStudio XML 契约](../../../output_format/packstudio/README.md)。
