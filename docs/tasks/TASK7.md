# TASK7：八类生产模板与参考数据运行时解耦

**状态**：已完成（2026-07-29）

## 1. 背景

TASK6 首版把 `flotherm_pack_data` 的目录、参数注册表、材料 JSON、基准和变体 FloXML 作为
运行时数据源。虽然能够快速复现已验证证据，但软件无法在参考目录缺失时独立运行，也使模板
行为受开发归档格式约束。用户明确要求参考目录只用于设计核对，八类模板必须在生产代码中
手写实现。

## 2. 目标

- `src/packstudio` 不读取或解析 `flotherm_pack_data`。
- 八类模板分别拥有生产字段定义、默认值、范围、条件联动和几何生成规则。
- 内置材料、BGA、Flip-chip、引线框、键合线、通孔和封装体均由生产代码生成。
- 保留经过复核的关键基准尺寸，但不在运行时打开基准 FloXML。
- 删除旧参考适配器，避免形成第二套可误用的生成路径。

## 3. 实现

### 3.1 原生模板库

- [x] 建立 `templates/package_library` 生产目录和八个模板模块。
- [x] 以 `TemplateDefinition` 显式声明字段、类型、默认值、范围、选项和条件。
- [x] 使用 schema v2 和按模板隔离的持久化键。
- [x] 模板目录声明 `packstudio_native` 和 `runtime_reference_data_required=false`。

### 3.2 手写几何

- [x] Bare Die：芯片尺寸、厚度、功率和翻转元数据。
- [x] Flip Chip CBGA/PBGA：基板、固定正交各向异性 bumps + underfill、芯片、
  BGA 和可选塑封/顶盖。
- [x] FBGA/FSBGA 与 Wirebond PBGA：基板、铜层、阻焊、通孔、die attach、芯片、
  塑封、键合线和 BGA。
- [x] QFN：DAP、底部焊料、四边离散引脚/焊料、芯片、键合线、塑封和可选 thermal land。
- [x] QFP：四边引脚、die flag、tie bars、芯片、键合线、塑封和可选 exposed pad。
- [x] SOIC：双边引脚、die flag、tie bars、芯片、键合线、塑封和可选 exposed pad。
- [x] 共享确定性矩形差集算法保证所有输出块无正体积重叠。

### 3.3 特殊约束

- [x] 仅 `has_bga=true` 的模板接受 BGA 配置和两种阵列表达。
- [x] BGA 仍为隐式全阵列，仅提供中央焊球、中央去球和显式去球。
- [x] Flip-chip 层没有离散/坍塌选项，始终为有厚度正交各向异性等效块。
- [x] Flip Chip CBGA 保持 5.3 mm BGA、1.8 mm bump 包络和已复核 Z 堆叠。

### 3.4 API 与清理

- [x] 主 API 改为 `/api/templates/{template_id}/*` 和 `/api/templates/materials`。
- [x] `/reference/*` 仅保留为隐藏兼容别名，调用同一个生产实现。
- [x] 前端目录改为 `features/package-library`，不再调用 reference 路径。
- [x] 删除 FloXML parser、reference repository、变体 patch 和动态材料读取器。

## 4. 验收

- [x] 8/8 原生模板可生成无重叠模型。
- [x] 8/8 PTA XML 可导出并解析，不含网格实体和求解结果。
- [x] 测试拦截所有 `Path.read_text` 和 `etree.parse` 后，8 类生成/导出仍成功。
- [x] `src/packstudio` 不含 `flotherm_pack_data`、JSON/FloXML 运行时读取。
- [x] 后端、前端、Ruff、ESLint 和生产构建通过。
- [x] 更新 TASK、ADR、README、PLAN 和提交说明，仅执行 `git add`。

## 5. 可信度边界

- `flotherm_pack_data` 继续作为开发期证据和回归依据，可以从部署包中移除。
- 字段和几何规则由 PackStudio 维护；新增参考变体不会自动改变软件行为，必须通过代码评审
  和测试显式实现。
- 原生模板保持轴对齐矩形块工程等效，不声称逐个复刻 FloTHERM PACK 的全部内部建模选项。
- 下游 PTA GUI 的导入、网格和求解仍需人工验收。
