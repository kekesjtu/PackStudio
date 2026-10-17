# 凸点与 BGA 组件选材

Flip Chip CBGA/PBGA 的“倒装芯片凸点”步骤提供“凸点焊料”和“底部填充材料”。
Bare Die 启用凸点后同样提供这两个字段。四类 BGA 模板的焊球步骤提供“BGA 焊球材料”。

- 焊料可从版本化材料库的 `Alloys (Solders)` 分类选择，underfill 从 `Others` 分类选择；
  该分类沿用已采集 PACK 向导 `dropdown_underfill_material.png` 的默认材料组。
- Flip Chip 默认凸点焊料、underfill 和 BGA 焊料分别从原生 `c4SolderMaterial`、
  `underfillMaterial`、`solderMaterial` 路径解析；Bare Die 使用模板 JSON 默认值。
- 修改所选材料物性只影响当前方案；显式选材随参数保存，切换 Footprint 时保留。
- 凸点仍生成有厚度的正交各向异性等效层。焊料和 underfill 一起参与三向导热率、
  密度与体积热容计算，不把整个等效层替换为某一种组分。
- BGA 等效表达消费当前焊料与静态空气的物性；离散表达的中央和外围焊球均使用当前焊料。
  去球区域保持静态空气。凸点焊料和 BGA 焊料可以分别选择。
- 对已有等效材料 ID 的显式物性覆盖仍具有最终优先级。导出继续使用当前模型的材料物性。

接口沿用 `material_assignments`，新增键为 `group-bump-solder`、`group-underfill` 和
`group-bga-solder`。组件选材仅接受模板 schema 中列出的材料；Bare Die 未启用凸点时，
API 拒绝对应的凸点材料赋值。
