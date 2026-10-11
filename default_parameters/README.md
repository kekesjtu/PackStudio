# 默认参数库

本目录是生产运行依赖，随源码、wheel 和桌面 EXE 分发。程序不需要 FloTHERM 安装目录，
也不读取开发证据目录 `flotherm_pack_data/`。JSON 是默认值的唯一维护入口。

## 数据组织

| 文件 | 内容 |
| --- | --- |
| `manifest.json` | 数据版本、342 条记录的家族计数、源快照及家族文件 SHA-256 |
| `flotherm/*.json` | 7 类 PACK `.des` 的完整无损转录，共 342 条 |
| `templates/*.json` | 8 类生产模板的字段、范围、条件、默认选材、已核验基线及基准材料 |
| `source_adapters.json` | 7 类源记录到生产字段的映射、派生规则、缺值策略与个别记录修正 |
| `adaptation_report.json` | 342 条参数审计、输入文件哈希及 510 种模型配置的生成/导出验收 |
| `materials.json` | 集中材料库默认物性、颜色、名称和来源 |
| `request.json` | BGA 配置、网格档位及 PTA 格式所需的初始温度占位值 |

342 条分布为 CBGA FC 49、PBGA FC 45、PBGA WB 36、Chip Array 38、QFN 46、PQFP 61、
TSOP conventional 67。Bare Die 的 4 个预设来自既有审核规格，不计入这 342 条。

## 转录契约

每条源记录保存 `id`、安装相对路径 `source_path`、源文件 SHA-256、`raw_fields` 和 `values`。
参数 JSON 使用 UTF-8/LF，manifest 与审计文件哈希以 LF 字节为准；安装研究快照的
换行也先规范为 LF 再计算快照哈希。`.des` 的 `source_sha256` 仍是原始供应商文件字节哈希。
`raw_fields` 保留原始字符串（包括空串、大小写与数字格式），`values` 将纯数字转为 JSON 数字，
空串转为 `null`，其他值保持字符串。数值没有换算单位；原始符号和枚举编号不自动解释。
`designDate` 等数字形字符串也按此词法规则解析，其原始表达始终可从 `raw_fields` 找回。

源文件通常包含未启用分支的空字段、由 PACK 推导的参数及材料名称，不能把空值一律填成零。
材料数值来自先前审核的基准模型，不能宣称仅凭 `.des` 的材料名称就获得了物性。

## 生产默认值

342 个源记录全部接入规格选择器；另保留 Bare Die 的 4 个规格，共 346 个选项。
运行时以 `source_adapters.json` 的字段映射读取 `flotherm/*.json`，逐项获取封装、芯片、
引脚、焊球、承载台和可用互连参数，不按外形尺寸统一缩放。`td` 给出芯片厚度时也参与联动。
源中未提供的基板厚度、金属层厚度、通孔行列等参数，从模板 JSON 或既有审核规格继承，
具体字段列于 `adaptation_report.json` 的 `parameter_audit.inherited_fields`。

2026-10-11 的[原生默认值调研](../docs/research/flotherm-native-defaults.md)发现，
仅 36 个 Wirebond PBGA 预设的基板厚度、键合线总数和过孔间距，就有 56 处生产值
与 PACK 默认分支不同。研究快照尚未接入本目录；现有生成/导出验收不代表默认值全部一致。

七个默认规格保留已对照 PACK 导出的基线，同时继续动态读取 `Ld/Wd`；其余源适配规格的
`preset_geometry_status` 为 `source-adapted`。保留此前选项的标识，旧方案仍可读取；
非默认规格现在采用原始源阵列，因此 PBGA_896 的网格从旧关联值 31×31 改为源定义 39×39，
去除中央 25×25 区域，球数为 896。

BGA 的 `MDp/MEp` 是全填充行数，去球区尺寸为 `MD-MDp` / `ME-MEp`；中央球用 `MDc/MEc`。
Chip Array 的 `balls` 列表声明现存球坐标，X 对应列、Y 对应行，补集转为显式去球单元。
去球区行列同时为 0 表示只应用显式去球，不额外去掉中央矩形。两个源具有该坐标列表。
46 个源的名称球数与可读取布局不同，保留源布局并显示提示，不凭名称猜测缺球位置。
PBGA_576 / PBGA_845 的区域奇偶不匹配，按负轴方向取整，中心偏移半个节距，界面提示
尚未完成原生 PACK 位置对照；一般用户配置仍默认要求中心对称。
QFN_3X3_6 采用双侧 6 引脚，Y 侧计数为 0，不生成该侧引脚及键合线。

源材料名称保留供审计；运行时继续采用各模板已经核验的等效材料张量，用户选材仍优先。
这不等于全部新规格已经与原生 PACK 输出逐块或逐物性核对，也不构成热仿真精度验证。

优先级保持为：字段默认值 → 选中预设的关联值 → 用户显式覆盖。Bare Die 尺寸预设包含厚度，
源规格的厚度来自源 `td`，七个默认基线采用审核字段默认值。默认选材只对当前启用的组件生效，用户选择优先。

加载器校验版本、字段类型、取值范围、预设目标与选材范围；文件缺失或不合法时显式失败，
没有代码中的备用数值。进程缓存读取结果，修改 JSON 后需重启后端。边界设置已移除；
PTA 的初始温度是文件格式占位值，不代表配置了环境温度或换热边界。

## 重现转录

```powershell
uv run --locked python tools/transcribe_default_parameters.py `
  flotherm_pack_data/installation/presets.json --output default_parameters
```

该脚本只更新源家族 JSON 与 manifest，不重写已审核的生产模板和材料默认值。
使用开发测试核对全部原始键值、计数和哈希；编辑源转录文件后也需同步 manifest 校验值。

```powershell
uv run --locked pytest tests/backend/templates/test_default_parameters.py `
  -o cache_dir=tmp/pytest --basetemp=tmp/pytest-default-library
```

## 重现适配验收

```powershell
uv run --locked python tools/validate_source_presets.py
```

报告包含 342 个源、510 种模型配置：168 个 BGA 规格分别验证等效和离散表达，
174 个非 BGA 规格各验证一次。检查正尺寸、无重叠、材料和分组引用、球数一致、
ECXML 安装版 XSD，以及 PTA XML 可生成和材料引用；测试不调用本机 PACK。
修改参数 JSON 后重新生成报告，随后执行后端测试，检查报告输入哈希仍对应当前参数库。

API 客户端选择规格时可以省略 `bga`，或只传需要覆盖的 BGA 字段；显式字段优先于源布局。
发送完整 BGA 对象即表示覆盖全部配置。界面切换规格会从 schema 的 `preset_bga` 更新布局，
并保留用户选择的表达方式、顶部结构、通孔/散热焊盘开关与功率。
