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

## PTA 几何构建模式

PackStudio 支持 PTA 的两种正交几何路径：

- 简单连续堆叠使用 `Layers/Layer/Blocks`；
- 高碎片结构使用根级 `Structure/Blocks`，并设置 `UseBlockBuildMode=true`。

根级块通过自身的 `ZOffsetExpression` 和 `ThicknessExpression` 设置 Z 位置与高度。同一
`Block/AllRects` 可包含多个矩形，`Add_sub=true` 表示加操作，`Add_sub=false` 表示减
操作。PackStudio 只在几何体积完全等价且不跨材料、逻辑源或热源密度时执行该压缩。
