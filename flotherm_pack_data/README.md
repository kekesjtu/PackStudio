# Flotherm PACK 原生参考数据

本目录保存可复现的 Flotherm PACK 原生样本，用于核对封装参数、选项行为和模型输出。命令和工具入口见 [PACK 原生扫参工具](../tools/pack_sweep/README.md)。

## 目录结构

```text
flotherm_pack_data/
  README.md
  index.json
  verification.json
  screenshots.json
  packages/<package>/
    index.json
    baselines/<context>/
    parameters/<context>/<component>/<property>/<value>/
    options/<context>/<component>/<property>/<value>/
    presets/<preset>/
    cases/<case>/
    screenshots/<view>.png
```

| 目录 | 收录内容 |
| --- | --- |
| `baselines` | 每个包型一个 `default` 基线，记录确定的原生创建选项。条件字段共用能激活它们的分支基线，例如 `encapsulant_with_slug`。 |
| `parameters` | 连续数值及计数参数的单变量变化。 |
| `options` | 布尔、枚举或单个材料选项的变化。创建窗口里的单个独立选项也归入此类。 |
| `presets` | 选择原生预设后导出的整套样本，例如 JEDEC 外形预设。每个预设一个目录。 |
| `cases` | 用单变量路径难以表达的补充样本，例如需要加载自定义去球矩阵的 DES。每个案例直接使用一个简短的语义目录名，例如 `cases/custom_ball_map/`。 |
| `screenshots` | 原生界面证据。文件名按页面或选项状态命名，例如 `die.png`、`bumped_die_enabled.png`。 |

## 命名与定位

- 包型目录沿用项目 ID，包括 `bare_die`、`cbga_fc`、`chip_array`、`pbga_fc`、`pbga_wb`、`pqfp`、`qfn`、`sop`。
- 上下文、组件、字段、枚举值、预设和案例名统一用小写英文字母、数字和下划线。组件和字段从 PACK 原生标识转换，例如 `dropInSlug/adhesivePresentUnderSlugFoot` 对应 `drop_in_slug/adhesive_present_under_slug_foot`。创建窗口的字段使用 `creation` 作为组件目录。命名转换发生冲突时，用稳定的语义名称区分，并在 `case.json` 中记录准确的原生标识。
- 布尔值使用 `true`、`false`。数值使用十进制，保留负号与小数点，省去多余的尾零，例如 `0.05`、`-0.1`、`12`。数值单位写在 `case.json` 中，路径使用该单位下的值。
- 样本以完整的库内相对路径标识。索引和对照引用使用以本目录为起点的相对路径，分隔符为 `/`。版本和运行顺序记录在元数据中。

| 样本 | 相对路径 |
| --- | --- |
| Bare Die 默认基线 | `packages/bare_die/baselines/default/` |
| 芯片长度取 4.41 mm | `packages/bare_die/parameters/default/die/die_length_ld/4.41/` |
| 网格密度选 Coarse | `packages/bare_die/options/default/modeling_options/grid_density/coarse/` |
| FC PBGA 包封层带散热块的分支基线 | `packages/pbga_fc/baselines/encapsulant_with_slug/` |
| 在该分支启用散热块支脚下的胶层 | `packages/pbga_fc/options/encapsulant_with_slug/drop_in_slug/adhesive_present_under_slug_foot/true/` |
| SOP 的 JEDEC 预设 | `packages/sop/presets/sop_28_7_6x17_9/` |

## 样本内容

每个基线、扫参点、选项点、预设和专项案例使用相同的文件名。

| 文件 | 内容 |
| --- | --- |
| `case.json` | 采集意图与输入。单变量点记录原生组件和字段标识、比较基线路径、基线值、目标值及适用单位。预设记录原生预设标识。专项案例记录联动变更、输入依赖或待核对的行为。 |
| `script.xml` | 可重放的 FloSCRIPT。脚本引用样本目录内的相对路径。 |
| `input.des` | 脚本加载的 DES 输入，仅依赖 DES 的案例提供。 |
| `model.des`、`model.xml` | PACK 导出的设计文件与 FloXML 模型，保留原生内容。 |
| `native_run.json` | PACK 版本与原生执行状态。 |
| `verification.json` | 脚本与 FloXML 的 XSD 校验、DES 回读和案例适用的行为核对结果。提供 PackStudio 对应请求的案例同时记录模型比对结果。 |

根索引列出全部包型和样本路径，包型索引列出所属基线与样本。`verification.json` 汇总验证结果与覆盖缺口，`screenshots.json` 记录截图路径及其所示的页面或状态。

## 重扫范围与发布

1. 为八个包型生成默认基线，再按字段启用条件补充共用的分支基线。基线记录完整的创建选项和分支前置条件。
2. `options` 扫全每个适用上下文中的选项及其全部合法取值，包括基线值。每个取值单独成点，其余设置沿用该上下文的基线。
3. `parameters` 中每个单参数在适用上下文中至少采集三个不同的有效取值，基线值另计。可行时覆盖基线两侧，其余参数保持基线设置。如果原生约束使可用的非基线值不足三个，采集所有可用值，并在验证汇总中记录缺口和原因。
4. 整套原生预设归入 `presets`。有明确验证需要时补充 `cases`。能用已有基线和单变量变化表达的样本归入 `parameters` 或 `options`，在 `case.json` 中记录验证目的。用原生回读和对应输出确认变更是否生效。对于只影响界面或保存状态的选项，记录对应证据和观察结果。
5. 审阅规范后，将当前数据目录完整归档到 `tmp/YYYY-MM-DD-pack-resweep/before-resweep.zip`，包含截图、索引与验证记录。ZIP 仅保存在本地。
6. 在同一任务目录中采集并验证新样本，完成后发布到本目录。发布保留本 README。新版截图按需要重新采集，已有截图随旧数据归档。发布时同步更新工具说明及仓库中引用样本的路径。
