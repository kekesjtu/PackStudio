# 输出格式

这里存放 PackStudio 所有输出文件格式的示例，作为 PackStudio 与下游求解器的接口契约。

## 目录结构

```text
output_format
└── cases_for_XXX/              # 假设以后需要增加新的输出格式，放在这里
└── cases_for_PTA/              # PTA 求解器输入格式
    ├── simple_steady_tests/    # 简单稳态测试用例
    ├── simple_transient_tests/ # 简单瞬态测试用例
    ├── nonlinear_steady_tests/ # 非线性材料稳态用例
    ├── microfluid_cases/       # 微流道散热用例
    └── simple_macromodel_cases/# 降阶宏模型用例（含 .tmm ROM 文件）
```

## PTA 分层几何约定

PackStudio 固定使用 PTA 的 `Layers/Layer/Blocks` 路径：

- 根级 `Structure/Blocks` 保持为空；
- `UseBlockBuildMode=false`；
- `Layers` 从顶层到底层排列，`TopLayerIndex=0`，只有第 1 层设置
  `IsTopLayer=true`。

只有第 1 个顶层 Layer 中的块允许 `ThicknessExpression` 与层厚不同；其他层内所有块均与
所属层等厚。顶层以下的跨层结构按层切片。同一 `Block/AllRects` 可以包含多个矩形，
`Add_sub=true` 表示加操作，`Add_sub=false` 表示减操作。PackStudio 只在几何体积完全等价且
不跨材料、结构、逻辑源、父组或热源密度时执行该压缩。
