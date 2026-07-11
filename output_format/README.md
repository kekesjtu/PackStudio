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
