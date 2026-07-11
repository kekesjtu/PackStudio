# Flip Chip CBGA / BGA 模板

## 功能范围

TASK2 当前只提供 `flip-chip-cbga` 模板。它把封装表达为与坐标轴平行的矩形块，支持：

- 基板、芯片、flip-chip bumps、underfill、BGA 焊球；
- 可选的热界面层、嵌入式散热块和顶盖；
- 全阵列、交错阵列、中央去球、中央焊球和自定义去球；
- 等体积离散方柱与正交各向异性等效块；
- 芯片均匀体热源，以及可选的顶面/底面对流边界；
- JSON 领域模型、浏览器三维预览和精简 PTA XML 导出。

## 坐标与默认模型

所有输入尺寸使用 mm。原点位于基板底面中心，X/Y 分别沿封装长宽方向，Z 向上。
BGA 焊球因此位于负 Z。默认参数生成 8 个矩形块，其模型树为：

```text
Flip Chip CBGA
├─ Substrate                  1 块
├─ Die                        1 块 + 1 W 均匀热源
├─ fc_bumps                   1 个 7×7 各向异性等效块
├─ Solder_ball                4 个外围均匀等效块
│  └─ Center_SBall            1 个中央 3×3 等效块
└─ Top structures             默认关闭
```

默认凸块和焊球物理数量均为 49。外围四块加中央一块只改变几何表达数量，不改变物理焊球
数量和等效体积分数。

## 阵列模式

| 模式 | 行为 |
| --- | --- |
| `full` | 所有单元有焊点；等效模式生成一个矩形块 |
| `staggered` | 相邻行 X 向错开半个 pitch；等效模式按行生成块 |
| `center_depopulated` | 对称中央区域去球；外围拆为四块，中央可省略或填 underfill |
| `center_populated` | 外围四块与中央阵列分组建模，适配任务参考模型树 |
| `custom` | 按单元索引去球，保留区域自动分割为无重叠矩形 |

界面中的自定义单元使用从 1 开始的“行,列”，例如 `2,2; 2,3`；JSON API 中的
`omitted_cells` 使用从 0 开始的 `row` 和 `column`。

中央模式要求中央行列数均为正、严格小于总行列数，并与外圈保持中心对称。自定义模式必须
至少保留一个阵列元素。

## 两种阵列表达

### 离散等体积方柱

直径为 `d` 的圆柱焊点用边长 `sqrt(pi) × d / 2` 的方柱替代。替代前后横截面积相同，
所以在层高不变时体积相同。启用“生成基体矩形块”后，每个单元剩余区域由四个互不重叠的
underfill 矩形块补齐。

### 各向异性等效块

实现采用 `docs/各向异性等效层/micro_c4_bump_underfill_anisotropic_layer_derivation.md`
第 4 节。对于半径 `r`、pitch `px × py`，填充率为：

```text
f = pi × r² / (px × py)
```

Z 向导热率按并联混合，X/Y 向分别按等体积方柱的串并联热阻计算。密度按体积分数混合，
比热按体积热容守恒计算。材料在 JSON 中以 `kx/ky/kz` 表达，在 PTA XML 的
`DaoreXishu` 中以 `kx,ky,kz` 表达。

## 校验规则

生成前会拒绝以下输入：

- 直径大于任一方向 pitch，或等体积方柱放不进单元；
- 芯片超出基板，凸块阵列超出芯片，焊球阵列超出基板；
- 散热块/顶盖未覆盖下方目标，或超出基板包络；
- 不对称中央区域、重复/越界的自定义去球索引；
- 材料 ID 冲突、材料缺失、组引用错误或矩形块正体积重叠；
- PTA 导出时出现不连续的 Z 层叠。

## API

后端启动后提供以下接口：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/api/templates` | 返回当前唯一模板及支持的模式 |
| `GET` | `/api/templates/flip-chip-cbga/defaults` | 返回完整默认参数 |
| `POST` | `/api/templates/flip-chip-cbga/generate` | 校验参数并返回 JSON 领域模型 |
| `POST` | `/api/templates/flip-chip-cbga/export/pta` | 生成可下载的 PTA XML |

前端使用“生成模型”刷新三维预览和模型树，使用“导出精简 PTA XML”按当前参数直接生成
XML。参数修改后，预览会标记为待重新生成。

## PTA XML 内容边界

导出文件包含几何、材料、热源、已启用边界和稳态热传递基础配置。焊球层的负 Z 坐标会在
导出时整体平移到 PTA 的非负层坐标，层间相对位置保持不变。

文件明确不包含：

- 任何 `Mesh*` 节点或网格实体；
- `Results`、`LayerPBResults`、`ThermalMaskResults`；
- PTA 求解过程生成的温度场、热流场及其他派生结果。

这些内容由 PTA 的网格与求解阶段生成。自动化测试会扫描 XML 节点，防止这些字段回流到
PackStudio 导出器。

## 验收命令

```powershell
conda activate PackStudio
python -m pytest -W error
python -m ruff check src tests
python -m ruff format --check src tests
npm run lint
npm test
npm run build
```
