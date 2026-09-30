# 默认参数库

本目录是生产运行依赖，随源码、wheel 和桌面 EXE 分发。程序不需要 FloTHERM 安装目录，
也不读取开发证据目录 `flotherm_pack_data/`。JSON 是默认值的唯一维护入口。

## 数据组织

| 文件 | 内容 |
| --- | --- |
| `manifest.json` | 数据版本、342 条记录的家族计数、源快照及家族文件 SHA-256 |
| `flotherm/*.json` | 7 类 PACK `.des` 的完整无损转录，共 342 条 |
| `templates/*.json` | 8 类生产模板的字段、范围、条件、默认选材、已验证预设及基准材料 |
| `materials.json` | 集中材料库默认物性、颜色、名称和来源 |
| `request.json` | BGA 配置、网格档位及 PTA 格式所需的初始温度占位值 |

342 条分布为 CBGA FC 49、PBGA FC 45、PBGA WB 36、Chip Array 38、QFN 46、PQFP 61、
TSOP conventional 67。Bare Die 的 4 个预设来自既有审核规格，不计入这 342 条。

## 转录契约

每条源记录保存 `id`、安装相对路径 `source_path`、源文件 SHA-256、`raw_fields` 和 `values`。
`raw_fields` 保留原始字符串（包括空串、大小写与数字格式），`values` 将纯数字转为 JSON 数字，
空串转为 `null`，其他值保持字符串。数值没有换算单位；原始符号和枚举编号不自动解释。
`designDate` 等数字形字符串也按此词法规则解析，其原始表达始终可从 `raw_fields` 找回。

源文件通常包含未启用分支的空字段、由 PACK 推导的参数及材料名称，不能把空值一律填成零。
材料数值来自先前审核的基准模型，不能宣称仅凭 `.des` 的材料名称就获得了物性。

## 生产默认值

当前保持 25 个已验证的 Footprint/芯片尺寸选项。21 个非 Bare Die 预设通过 `source` 指向
源记录，通过 `source_values` 将 `Ld/Wd` 映射为 `die.length/die.width`；生成 schema 与模型时
实际读取这些源 JSON。其余关联参数保留经现有 FloXML 回归验证的独立默认值。

全部 342 条已经持久化；其余源记录尚未全部开放为生产选项，原因是字段、选项编号、材料与
几何生成规则还需逐族映射和验证，并非它们普遍缺少芯片尺寸。新增选项应在模板 JSON 中声明
独立关联值/来源映射，校验生成几何后纳入回归，禁止按统一比例缩放整个封装。

优先级保持为：字段默认值 → 选中预设的关联值 → 用户显式覆盖。Bare Die 尺寸预设包含厚度，
因此改字段默认厚度不会覆盖选中预设的厚度。默认选材只对当前启用的组件生效，用户选择优先。

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
