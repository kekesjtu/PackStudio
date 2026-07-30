# TASK9：手写模板的 FloXML 几何保真纠偏

**状态**：已完成（2026-07-30）

## 1. 背景

TASK7 正确地移除了 `flotherm_pack_data` 运行时依赖，但首版“手写模板”把部分参考结构重新
设计成了猜测性通用几何。用户进一步明确：参考目录可以从部署包移除，但生产模板必须把已经
验证的 UI、参数、基准 FloXML 和单变量差异转录成代码；“不依赖”不等于可以改变模板结构。

## 2. 目标

- 生产运行继续不定位、读取或解析 `flotherm_pack_data`。
- 八类默认模板的原始 cuboid 坐标、尺寸和材料属性忠实转录基准 FloXML。
- 生产向导已映射的数值字段按单变量 FloXML 差异实现几何联动。
- Flip-chip 顶盖分支不再使用猜测性几何。
- 保留用户明确规定的 BGA、Flip-chip 和 TASK5 矩形分区特例。

## 3. 实现

### 3.1 坐标与基准模型

- [x] 坐标原点统一为 FloTHERM PACK 的封装底平面中心，BGA 从 `z=0` 向上生成。
- [x] Flip Chip CBGA/PBGA 的基板、凸点层和芯片改为 `0.4 → 1.55 → 1.65 → 2.26 mm`
  基准堆叠。
- [x] FBGA/FSBGA、Wirebond PBGA、QFN、QFP、SOIC 的基板铜层、通孔、DAP、引线框、
  die flag、tie bar、键合线、阻焊与塑封均按基准 cuboid 拓扑重写。
- [x] Bare Die 保持已匹配的单块基准。

八类默认原始 cuboid 数量为：

| 模板 | cuboid 数 |
| --- | ---: |
| Flip Chip CBGA | 4 |
| Flip Chip PBGA | 4 |
| Wirebond PBGA | 49 |
| FBGA / FSBGA | 65 |
| QFN | 314 |
| QFP family | 44 |
| SOIC family | 24 |
| Bare Die | 1 |

### 3.2 参数联动与材料

- [x] 把 QFN 的 DAP/引脚共同厚度、键合端点、蚀刻和暴露长度联动改为差异证据公式。
- [x] 修正 FBGA 与 Wirebond PBGA 各自不同的 via 起始信号层规则。
- [x] 修正 QFP gap 对 tie-bar 填充高度的双向平均规则。
- [x] 修正 SOIC flag、gap、die/lead 高度关系及 die 高于/低于 lead 顶面时的键合竖段方向。
- [x] BGA 等效材料按全阵列实际包络而不是理想节距单元计算，恢复基准体积分数和三向物性。
- [x] 内置基准有效材料、静态空气、粘接、塑封、引线框和顶盖材料的转录属性。

### 3.3 Flip-chip 顶部结构

- [x] 顶部结构提供 `bare_die`、`lid`、`plate`、`encapsulant` 四个已验证分支。
- [x] lid 使用顶板、四段侧壁、四段侧壁粘接和 die attach 的参考拓扑。
- [x] plate 使用热板和 die attach；encapsulant 使用基板顶面起算的独立长宽厚。
- [x] 删除旧的 0.8 倍 TIM、铜盖和从 `z=0` 淹没整个封装的猜测实现。

### 3.4 特殊规则

- [x] 只有 BGA 层提供正交各向异性等效与离散两种表达。
- [x] Flip-chip bumps + underfill 保持有厚度正交各向异性等效层；不复刻参考中的各向同性
  bump 材料、坍塌层或离散选项。
- [x] BGA 仍为隐式全阵列，仅保留中央焊球、焊球去除和显式去球组合。
- [x] 原始 FloXML 可有嵌入/重叠 cuboid；生产输出继续按 TASK5/ADR-0005 优先级切分成无
  正体积重叠矩形块。

## 4. 验证

- [x] 8 类默认几何：逐 cuboid 原点、尺寸和数量完全匹配基准 FloXML。
- [x] 8 类默认材料：除强制改造的 Flip-chip bumps 层外，逐 cuboid 热物性匹配基准。
- [x] 320 个已映射数值高/低单变量：逐 cuboid 几何匹配对应 FloXML。
- [x] 6 个 Flip-chip 顶盖分支基线和 48 个分支数值变体：逐 cuboid 几何匹配。
- [x] 生产源码仍不包含参考目录访问；拦截文件读取后 8 类生成和 PTA 导出通过。
- [x] 后端 468 项、前端 17 项测试通过；Ruff、ESLint 和生产构建通过。

## 5. 可信度边界

- 单变量几何回归不等于所有任意多参数组合都由 FloTHERM PACK 回放验证。
- 默认有效材料已逐块核对；除 BGA/Flip-chip 专用等效算法外，本任务不宣称所有有效材料在
  任意参数组合下都逐变体复刻 FloTHERM PACK 内部算法。
- 最终 PTA GUI 导入、网格和求解仍是交付前人工验收项。
