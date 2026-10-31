# 四层基板创建参数与金属层

## 原生证据

- [Chip Array 创建输入](../template/chip_array/chip-four-layer/case.json) 和 [Wirebond PBGA 创建输入](../template/pbga_wb/wb-four-layer/case.json) 均记录 `substrateLayer=4-Layer`、`solidPlaneThickness=0.036`，以及上下信号层厚度 `0.018`（mm）。
- 对应原生分支记录见 `runtime_data/presets/chip_array/ChipArray_24_4X4mm_0_8.json` 和 `runtime_data/presets/pbga_wb/PBGA_121_15X15mm.json` 的 `branches.four_layer.groups.metalLayers`。两条内部金属层记录均为 0.036 mm；所记录的深度从基板顶部量起。
- 原生采样记录注明：`gap=(A2-top-bottom-2*solid)/3`，两个内层深度分别为 `top+gap`、`top+2*gap`。现有样本的 A2 为 0.56 mm，top、bottom 为 0.018 mm，因此两个内层深度为约 0.168667 和 0.319333 mm。

现有证据覆盖 0.036 mm 的原生创建值及其生成表格；其他厚度的原生界面取值范围与响应未在该记录中验证。
