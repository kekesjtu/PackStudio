# FC 顶盖侧壁与芯片重叠

FC PBGA 和 FC CBGA 的 `49_6X6mm` 原生预设选用顶盖时，`6 mm × 6 mm` 的顶盖采用 `2.5 mm` 的侧壁宽度，中央开口只有 `1 mm × 1 mm`，金属侧壁侵入 `1.8 mm × 1.8 mm` 的芯片。两家族的 `64_7X7mm` 预设也有同样的尺寸冲突。

PackStudio 将这四个预设的顶盖侧壁宽度设为 `2.0 mm`。顶盖开口长宽分别为外部尺寸减去两倍侧壁宽度。选择顶盖时，输入校验要求开口容纳芯片。启用加强环时，以加强环内孔作为开口。开口边缘可以与芯片共面。

原生默认导出见 [FC PBGA](../../../flotherm_pack_data/packages/pbga_fc/options/default/creation/top_cover/lid/model.xml) 和 [FC CBGA](../../../flotherm_pack_data/packages/cbga_fc/options/default/creation/top_cover/lid/model.xml)。
