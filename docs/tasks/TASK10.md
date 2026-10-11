# TASK10：封装模板分类与死代码治理

**状态**：已完成（2026-07-30）

## 1. 背景

TASK9 完成保真纠偏后，八类生产模板仍平铺在 `package_library` 根目录，共享基础设施、BGA、
Flip-chip 和引线框架实现混杂。前端同时保留了一套已被通用八类向导替代、从应用入口不可达
的 Flip Chip CBGA 专用工作区，增加了维护和误改风险。

## 2. 目标

- 按封装类别组织八类手写模板，不改变模板 ID、API、schema、几何或导出结果。
- 将共享生成基础设施与具体封装实现分开。
- 删除能够证明从生产入口不可达的旧前端代码、专属样式和失效测试。
- 保留仍被 API 或生产阵列算法调用的后端兼容实现。
- 用自动化测试固定新的目录边界。

## 3. 实现

### 3.1 后端模板分类

| 目录 | 职责 |
| --- | --- |
| `package_library/core/` | schema、请求、材料、几何归一化、生成器和跨类别矩形基元 |
| `package_library/bga/` | FBGA/FSBGA、Wirebond PBGA、BGA 层、via 与字段 |
| `package_library/flip_chip/` | Flip Chip CBGA/PBGA、顶盖、凸点等效层与公共字段 |
| `package_library/leadframe/` | QFN、QFP、SOIC 及其引线框几何 |
| `package_library/bare_die/` | Bare Die 单独模板 |
| `package_library/catalog.py` | 八类模板唯一注册入口 |

- [x] 将 BGA 与 Flip-chip 混合的旧 `layers.py` 拆为类别层构建器。
- [x] 将 via 基元归入 BGA，共用键合线和矩形环保留在 `core`。
- [x] 根目录只保留 `__init__.py` 和 `catalog.py`。
- [x] API 和测试导入迁移到新路径，没有建立掩盖旧结构的兼容转发文件。

### 3.2 前端死代码清理

- [x] 删除旧 Flip Chip CBGA 专用 `Workspace`、属性导航、九组属性面板、旧材料面板、
  旧参数持久化、预设和旧 API 客户端。
- [x] 删除只验证上述已删除模块的 3 个测试文件。
- [x] 删除 RowResizer 和对应无引用 CSS。
- [x] 将仍在使用的模型预览、模型树、材料字段、数值输入和列宽调整迁至
  `features/model-editor/`。
- [x] 将通用模型类型与旧 Flip-chip 专用请求类型分离，删除不再消费的专用类型。
- [x] 清除旧摘要、阵列指标、旧材料编辑器等无引用样式。

### 3.3 明确保留项

`src/packstudio/templates/cbga_fc/` 不属于死代码：现有兼容 API 仍调用其生成器，
新模板库的 BGA 分区和等效材料也复用其中经过 TASK5 验证的阵列算法，因此本任务保留。

## 4. 验证

- [x] 新增 8 个类别模板可导入测试和 1 个根目录结构约束测试。
- [x] Python 单次出现定义审计除 FastAPI 装饰路由外无结果。
- [x] TypeScript 单次出现导出审计无结果。
- [x] CSS 类审计只剩动态列宽类和 MUI 嵌套选择器例外。
- [x] 后端 477 项测试通过。
- [x] 前端 8 项现行测试通过；ESLint 和生产构建通过。
- [x] 八类 FloXML 基准与变体回归仍包含在后端全量测试中。

## 5. 验收

- [x] 生产模板按类别可定位，根目录不再平铺具体实现。
- [x] 不删除运行中或测试中仍被调用的后端定义。
- [x] 删除的前端代码从生产入口不可达，现行工作区功能未回归。
- [x] 单文件不超过 300 行，无调试残留或注释掉的实现。
