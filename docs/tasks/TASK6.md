# TASK6：八类证据驱动封装向导与统一矩形块生成

> **后续变更**：TASK7 已将本任务的运行时参考数据适配器替换为八类手写生产模板。
> `flotherm_pack_data` 现仅用于开发期参考和回归，不再是软件运行依赖。

**状态**：已完成（2026-07-29）

## 1. 目标

以 `flotherm_pack_data` 中通过最终验证的 8 类模板 UI、589 项参数注册表、8 份基准
FloXML、656 组单变量差异和 48 项材料定义为证据，沿 TASK1–5 主线把 PackStudio 扩展为
较完整的参数化封装模板库。生成结果统一使用 mm、笛卡尔坐标系和轴对齐矩形块，并继续输出
可由 PTA 打开、网格和求解器接管的输入 XML。

## 2. 数据契约与模板范围

| 模板 ID | 向导名称 | 基准来源 |
| --- | --- | --- |
| `flip_chip_cbga` | Flip Chip CBGA | `templates/flip_chip_cbga` |
| `flip_chip_pbga` | Flip Chip PBGA | `templates/flip_chip_pbga` |
| `wirebond_pbga` | Wirebond PBGA | `templates/wirebond_pbga` |
| `fbga_fsbga` | FBGA / FSBGA | `templates/fbga_fsbga` |
| `qfn` | QFN | `templates/qfn` |
| `qfp_family` | QFP family | `templates/qfp_family` |
| `soic_family` | SOIC family | `templates/soic_family` |
| `bare_die` | Bare Die | `templates/bare_die` |

- 向导字段、默认值、控件、可选值和显示/启用依赖来自
  `internal_property_registry.json`，不重新猜测 FloTHERM PACK 内部属性。
- 可执行值和可信区间来自 `parameter_coverage.json` 及对应变体。离散/枚举参数仅使用已回放
  值；连续参数只在双侧单变量证据可形成稳定几何关系时开放区间输入。
- 基准材料来自 `materials/master_material_library.json`。用户编辑后的材料定义按 ID 绑定到
  结构，不修改参考数据。
- 基准 FloXML 是参考证据，不直接作为 PackStudio 输出；其 cuboid、材料和源项转换为统一
  领域模型后再由 PTA 导出器序列化。

## 3. 强制建模规则

### 3.1 BGA 焊球层

- 只有 BGA 焊球阵列层提供“正交各向异性等效层”和“离散建模”两种表达。
- 默认排布隐式为正交全阵列，不提供 `pattern`、交错阵列或其他复杂 pattern。
- 只保留可独立组合的“中央焊球”和“焊球去除”；显式去球优先于中央焊球，中央焊球优先于
  对称中央去球。
- 去球区和离散单元间隙固定使用静态空气。外围、中央和空气掩码按 ADR-0005 的确定性矩形
  分区生成，块之间不得有正体积重叠。
- 全阵列外包络使用 FloXML 已验证规则：
  `((columns - 1) * pitch + diameter) × ((rows - 1) * pitch + diameter)`。

### 3.2 Flip-chip bumps + underfill

- 不复刻 FloTHERM PACK 的坍塌层、各向同性均质层或离散选项。
- 只生成有真实厚度的正交各向异性等效层。
- 等效物性使用 ADR-0002 与推导文档第 4 节的串并联热阻、质量和体积热容守恒公式；组分
  采用手工验证的 `Solder (Pb90/Sn10)` 与 `Flip-Chip Underfill (Typical)`。

### 3.3 Flip Chip CBGA 复核

- 基板、芯片、凸点、焊球、顶盖/塑封/slug 的基准坐标和尺寸从基准 FloXML 建立回归快照。
- 现有 `rows * pitch` 阵列外包络等猜测性公式必须删除或由差异证据修正。
- 参数变动必须由对应单变量 FloXML 差异证明；没有证据的派生关系不得标记为已验证。

## 4. 实施阶段

### 4.1 证据适配层

- [x] 建立 8 类模板目录、字段 schema、已验证值/区间和材料库读取器。
- [x] 将基准/变体 FloXML 的 cuboid、材料、热源和装配层级转换为稳定场景对象。
- [x] 对参考模型中的嵌入式 cuboid 做确定性矩形布尔拆分，生成无正体积重叠块。
- [x] 为每个生成模型记录参考版本、基准文件、应用的覆盖项和证据级别。

### 4.2 领域生成与特殊层

- [x] 实现 8 类基准模型与已验证参数覆盖的生成。
- [x] 实现四类 BGA 模板的统一焊球层、组合优先级、静态空气和两种表达。
- [x] 实现两类 Flip-chip 模板固定厚度正交各向异性 bumps + underfill 层。
- [x] 修正 Flip Chip CBGA 基准包络、Z 堆叠和参数联动。
- [x] 提供共享材料编辑、芯片热源、环境/PCB/顶部边界和三档最大网格尺寸。

### 4.3 API、向导与导出

- [x] 模板目录 API 返回 8 类模板及能力声明。
- [x] 每类模板提供 schema/defaults、生成和 PTA 导出 API。
- [x] 前端提供模板选择、分步字段导航、条件联动、BGA 专用入口、材料/模型树和三维预览。
- [x] 参数持久化按模板和 schema 版本隔离。
- [x] PTA 导出支持参考模型的多结构 Z 分层，仍不生成网格实体或求解结果。

### 4.4 验证

- [x] 8/8 基准模型均可生成、预览并导出。
- [x] 逐模板核对 cuboid 外包络、材料引用、热源功率和装配分组。
- [x] 双侧数值变体和枚举/布尔变体形成自动回归样本。
- [x] BGA 四种组合状态、两种表达及显式去球优先级通过测试。
- [x] Flip-chip 层始终为有厚度正交各向异性块，API 不接受其他表达。
- [x] Flip Chip CBGA 的 5.3 mm 基准焊球包络、1.8 mm 凸点包络和 Z 堆叠通过回归。
- [x] 后端、Ruff、前端测试、ESLint 和生产构建全部通过。
- [x] 更新相关 ADR/README/PLAN，生成提交说明并执行 `git add`，不执行 `git commit`。

## 5. 非目标与可信度边界

- 不把 FloTHERM PACK 的网格实体、结果、监视器或辐射设置复制到 PackStudio。
- 不宣称未经单变量回放覆盖的任意多参数组合与 FloTHERM PACK 完全等价；生成元数据应明确
  区分“基准复现”“单变量证据内插/精确变体”和“用户组合”。
- 不实现圆柱、球、任意旋转体或曲线引线；所有构件继续使用轴对齐矩形块等效。
- 不自动执行 Git commit。

## 6. 验收结果

- 参考数据验证：8/8 模板、369 个执行目标、123 个分支基线、656 个单变量变体和
  779 个预期导出通过，失败 0。
- 后端：71 项 pytest 通过；8 类基准模型均无正体积重叠，8 类 PTA XML 均可解析且不含
  `<Mesh>`、`Results`。
- 前端：6 个测试文件、16 项测试通过；ESLint 与 TypeScript/Vite 生产构建通过。
- Python：Ruff 规则与格式检查通过；所有生产代码和测试文件不超过 300 行。
- 生产构建仍提示主 JS chunk 大于 500 kB；这是性能优化项，不影响本任务功能验收。
