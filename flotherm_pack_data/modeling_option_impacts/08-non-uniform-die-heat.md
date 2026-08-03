# Non-uniform Die Heat

## 定义

| 项目 | 内容 |
|---|---|
| 内部属性 | `die.nonUniformDieHeat` |
| 值 | `false` / `true` |
| 模板 | 全部 8 类模板 |
| 默认 | `false` |

## 建模影响

默认 `false` 时，die 上有一个覆盖整个 die 面的 `DieSource`，引用统一的 `dieHeat`
source attribute。单独切换为 `true` 后，8 类模板均移除该 source 实体和对应 source
attribute，但没有自动增加分区热源。

这不是“功率变为零”的最终业务语义，而是 PACK 进入非均匀热源编辑模式后，等待用户
通过编辑器提供分区/热图。当前单变量案例没有编辑器内容，所以导出为空。

## PackStudio 生成规则

```text
if not non_uniform:
    emit one full-die source(power = package_power)
else:
    require heat_regions
    assert abs(sum(region.power) - package_power) <= tolerance
    emit one source per clipped heat region
```

若没有 `heat_regions`，PackStudio 应报验证错误，不能静默输出无热源模型。

## 数据边界

当前数据确认了模式切换和 uniform source 的删除，但没有捕获热图编辑器的数据格式或
区域重叠规则。

## 证据

- `../templates/*/xml_variations/option_switches/*nonuniformdieheat_true/`
