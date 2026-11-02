# FloSCRIPT 本机操作说明

本文面向本机 Windows 环境，说明如何使用项目工具调用 FloTHERM PACK、执行
FloSCRIPT 并导出原生 FloXML。命令在项目根目录运行，Python 使用 uv 管理的仓库环境。
文档描述通用操作、运行约定和检查方法。

批量模板扫参、完整归档和参考库重建使用
[tools/pack_sweep](tools/pack_sweep/README.md)，其底层执行统一调用本文的 `tools.floscript`。

## 本机路径

| 用途 | 路径 |
| --- | --- |
| 项目 | `E:\Users\mydearlong\Desktop\PackStudio` |
| PACK 安装根目录 | `E:\Program Files\Siemens\SimcenterFlotherm\2504` |
| PACK 程序 | 安装根目录下 `WinXP\bin\flopack.exe` |
| 本机程序版本 | `2025.13.1.1142` |
| PowerShell 7 宿主 | `C:\Users\mydearlong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe` |
| FloSCRIPT Schema | 安装根目录下 `examples\FloSCRIPT\Schema\FlopackFloSCRIPTSchema.xsd` |
| FloXML Schema | 安装根目录下 `WinXP\PlugIns\XML_PLUGIN_SCHEMA\xmlSchema.xsd` |

这些本机路径集中定义在 `tools/floscript/environment.py`。
工具固定调用上述 PowerShell 7，以隐藏窗口方式启动 PACK。
程序实际文件版本及二进制哈希写入每次运行记录。

先检查路径：

```powershell
uv run --locked python -m tools.floscript check
```

该命令检查运行文件和目录是否存在。许可证可用性及实际导出能力通过运行 PACK 验证。

## 编写与查询脚本

FloSCRIPT 的 PACK 脚本根节点为 `flopack_xml_log_file`，`version` 为 `1.0`。
脚本和模型都可能使用 `.xml` 扩展名，应根据根节点和用途区分。

常用命令职责：

| 命令 | 职责 |
| --- | --- |
| `new_package` | 创建封装，子节点 `new_value` 设置初始化参数 |
| `load_des` | 加载保存的设计 |
| `modify_component` | 修改指定组件的属性 |
| `modify_component_table_row` | 修改表格中的属性值 |
| `create_material`、`modify_material` | 在当前隔离材料库中创建或修改材料 |
| `save_des` | 保存当前设计 |
| `export_floxml` | 将当前模型导出为 FloXML |
| `quit` | 结束运行器启动的 PACK 进程 |

查询命令结构时读取本机 `FlopackFloSCRIPTSchema.xsd` 及其引用的
`FlopackCommands.xsd`、`CommonCommands.xsd`。
Schema 能检查命令和属性的结构，但部分属性名称及属性值采用自由字符串，
属性含义结合本机帮助、PACK 的脚本录制功能和参数回读确认。

组件名、属性名、枚举内部值区分大小写，以 Schema、本机帮助、脚本录制与参数回读确认。
先确定结构与选项，再设置受其影响的参数；脚本赋值与 PACK 初始值或加载设计的值共同确定输入。
输入单位应按对应属性的本机定义确认。

生成脚本时使用 XML 库写入动态属性，正确转义路径、名称和字符串。
`tools.floscript.script` 提供 `new_package_element`、`component_element` 和 `write_xml`。

## 执行已有脚本

以下变量中的脚本路径填写实际文件；每次执行使用独立的新运行目录。

```powershell
$packScript = '待执行的 FloSCRIPT 文件绝对路径'
$packRun = Join-Path (Get-Location) 'tmp\floscript-run-001'

uv run --locked python -m tools.floscript validate --script $packScript
if ($LASTEXITCODE -ne 0) { throw 'FloSCRIPT XSD 校验失败' }

uv run --locked python -m tools.floscript run `
    --script $packScript --output $packRun --timeout 60
if ($LASTEXITCODE -ne 0) { throw "执行失败，请检查 $packRun 中的日志" }
```

`run` 会再次校验脚本，准备隔离环境，执行 PACK，再检查产物。
它要求脚本至少包含一个 `export_floxml`。
默认等待 60 秒，可通过 `--timeout` 设置 1 至 86400 秒。
超时会终止运行器启动的 PACK 进程树，并保存运行记录。

文件路径规则：

- `load_des` 的相对输入路径以原始脚本所在目录为基准。
- `save_des`、`export_floxml` 的相对输出路径以运行目录为基准。
- 上述命令的路径会转换为绝对路径，写入运行目录中的 `replay.xml`。
- 各输出使用运行目录内的独立新路径，与工具运行文件分别命名。
- 多个 FloXML 输出的文件主名必须各不相同，用于运行记录中的索引。
- 同一脚本先保存再加载 DES 时，加载命令应使用该运行产物的绝对路径。

规范化脚本以 `quit` 结束，工具在脚本末尾补充所需的退出命令。
嵌套执行的 `project_run_script` 需要先展开为单个脚本，再执行和校验全部输出。
其他带文件参数的命令保留原有内容；应显式提供适当的绝对路径。

## 运行目录与材料库

工具为每次运行准备：

| 文件或目录 | 用途 |
| --- | --- |
| `replay.xml` | 规范化后实际执行的脚本 |
| `run_pack.ps1` | 运行启动器快照 |
| `runtime.json` | 安装来源和材料库准备方式 |
| `config/` | 本机安装配置的文件副本 |
| `central/flopack/` | 隔离的 PACK 数据和材料库副本 |
| `user/` | 隔离用户目录 |
| `temp/` | 进程使用的 `TEMP`、`TMP` |
| `stdout.txt`、`stderr.txt` | PACK 标准输出与错误输出 |
| `launcher-stdout.txt`、`launcher-stderr.txt` | PowerShell 启动器输出 |
| `LogFiles/` | PACK 原生日志 |
| `process.json` | 原生进程状态 |
| `run.json` | 汇总状态、检查结果和运行文件信息 |

脚本声明的 DES、FloXML 文件也保存在运行目录内。

默认复制安装目录中的用户材料库 `flocentral\flopack\Library`。
需要完全隔离用户材料时，添加 `--empty-material-library`，保留内置数据并使用空的用户材料库。
设计引用自定义材料时，材料库副本需要包含相应记录。

`FLOPRODUCTCONFIG`、`FLOTRANSLATIONS`、`FLOCENTRALDIR`、`FLOUSERDIR`、
`TEMP`、`TMP` 以及程序路径、Qt 插件路径仅在启动器及其子进程中设置。
`TEMP/TMP` 指向运行目录内可写的 `temp/`，供 DES 保存、加载与原生进程使用。

## 检查结果与故障定位

命令退出码为 `0` 时，`run.json` 的 `status` 应为 `success`。
失败与超时状态分别为 `failed` 和 `timed_out`，并返回对应失败退出码。
脚本预检失败时直接打印原因；原生启动后发生的失败会整理到 `run.json`。

成功检查覆盖：

- FloSCRIPT 通过本机对应 XSD。
- PACK 正常退出，原生日志可解析，`ERROR` 消息数为 0。
- 预期产物由该次运行生成，文件大小大于 0。
- 保存的 DES ZIP 含一个可读取的 DES 参数成员。
- 每个 FloXML 通过本机对应 XSD。

`run.json` 保留原生退出码、耗时、文件版本、程序及相关 DLL 哈希、
启动器哈希、输入路径，以及各产物的路径和大小。
`checks` 分别记录脚本结构、输出完整性和 FloXML 结构的检查结果。

失败时先查看 `errors`，再检查启动器输出、PACK 输出和 `LogFiles/`。
原生进程异常退出时，保存已有日志；重新执行使用独立目录。
执行结果以 `run.json`、进程状态、日志和该次生成的产物共同判定。

具体参数是否生效，需要回读保存的 DES，并按任务要求检查模型内容。
几何、材料、功率符合预期，以及目标软件的导入、网格和求解验收，由具体任务负责。

需要单独校验某个导出文件时：

```powershell
$packOutput = '待校验的 FloXML 文件绝对路径'
uv run --locked python -m tools.floscript validate --script $packOutput --floxml
```

## Python 调用与维护边界

公共能力位于 `tools/floscript/`：

- `environment`：本机路径检查、配置与材料库准备。
- `script`：命令构造、XML 写入、路径处理与两类 XSD 校验。
- `des`：`read_des` 读取保存的参数；`write_des` 创建仅含参数的 DES ZIP。
- `runner`：`run_script` 执行已有脚本；`replay` 执行带唯一 ID 和命令列表的批次。
- `runner.prepare_replay`：只准备批次；`runner.execute`：执行已准备的目录。

Python 接口和命令行默认都复制用户材料库；使用 `copy_materials=False` 选择空用户材料库。
`write_des` 写入参数 ZIP，设计附件由调用方在加载前准备。
安装目录中的原始文本 DES 与 PACK 保存的 ZIP DES 属于不同读取场景。

对于由 Python 接口准备的目录，使用：

```powershell
$packPrepared = '已准备的运行目录绝对路径'
uv run --locked python -m tools.floscript run --prepared $packPrepared
```

保持单一 PACK 启动实现 `run_pack.ps1`。新增任务调用公共接口，
将任务专属的参数映射与模型断言留在调用方。

通用工具的回归检查：

```powershell
uv run --locked pytest tests/research/test_floscript.py
uv run --locked ruff check .
```
