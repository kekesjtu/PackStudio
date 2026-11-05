# PackStudio XML v1

文件扩展名为 `.packstudio.xml`，编码为 UTF-8。根节点为 `<model version="1" name="方案名称">`，
直接子节点依次为一个 `materials`、一个 `sources` 和一个或多个 `group`。
文件只包含轴对齐长方体块、材料物性与按块关联的体热源，不需要读取 PackStudio 材料库。

所有数值最多输出 12 位有效数字，使用小数点 `.`，省略无意义的尾零；小数值可使用科学计数法，
不按固定小数位截断。零统一写为 `0`，不输出负零。此规则仅作用于导出文本，内部计算保留 `double` 精度。

## 材料

`materials/material` 的 `id` 是文件内局部编号（例如 `m1`），`name` 为显示名称，`type` 为导热类型：

| type | 含义 | 字段 |
| --- | --- | --- |
| `isotropic` | 常量各向同性 | 三方向导热率相同 |
| `orthotropic` | 正交各向异性 | 三方向导热率独立；数值相同也保留此类型 |
| `temperature_dependent` | 温度相关各向同性 | 三方向参考导热率相同，另含 `coefficient` 和 `reference_temperature` |

每个材料有 `density`（kg/m³）、`specific_heat`（J/(kg·K)）和 `conductivity`。
`conductivity` 的 `x/y/z` 属性为 W/(m·K)，均取当前模型的有效物性；等效材料在生成阶段完成计算。
温度相关材料的 `coefficient` 为导热率温度系数（W/(m·K²)），`reference_temperature` 为 K，
下游使用 `k(T) = k_ref + coefficient × (T - reference_temperature)`。
不输出未启用的材料存储字段、运行库 ID、颜色、分类、来源或等效配方。

## 组与块

`group` 的 `id` 在文件内唯一，`name` 为内部模型组的显示名称。每组有一个或多个 `block`，
以及一个文本值为局部材料编号的 `material`。材料不逐块重复，同一内部组含多种材料时分组输出。

`block` 的 `id` 全文件唯一，`name` 为显示名称。`x/y/z` 为块在统一笛卡尔坐标系中的各轴最小坐标，
`dx/dy/dz` 为严格正的尺寸，均为 m。组没有位移或旋转，块可以具有负坐标，所有数值必须有限。
输出保留生成模型中的块及重叠关系，不在导出时进行几何裁剪。

## 热源

`sources/source` 的 `block` 属性引用块 ID，`power` 为施加在该块体积上的总功率（W）。
同一块的多个功率项合并为一项；芯片切分后的功率分配由生成模型给出。无热源时输出 `<sources/>`。

## 字段边界

仅允许上述结构；无辐射或网格字段、`position`、`collapse`、`region`、监视点、边界条件或 notes。
内部网格参数保留在方案与建模核心中。下游自行设置网格、边界条件和求解过程。

示例：[bare-die.packstudio.xml](bare-die.packstudio.xml)。
