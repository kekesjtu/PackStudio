# PACK 原生扫参工具

在仓库根目录通过 uv 运行。需要已安装并可运行的 Flotherm PACK。可用 `--installation` 指定安装位置，默认位置见 [FloSCRIPT 本机操作](../../FLOSCRIPT.md)。

数据结构、命名与采样规则见 [原生参考数据](../../flotherm_pack_data/README.md)。

## 归档与重放

```powershell
uv run --locked python -m tools.pack_sweep archive --archive tmp/YYYY-MM-DD-pack-resweep/before-resweep.zip
uv run --locked python -m tools.pack_sweep rebuild --work tmp/YYYY-MM-DD-pack-replay
uv run --locked python -m tools.pack_sweep validate
```

`archive` 将完整参考目录写入本地 ZIP。`rebuild` 读取源库索引、各点的 `case.json` 及需要的 `input.des`，调用 PACK 重新导出并校验。源库默认是 `flotherm_pack_data/`，也可用 `--source` 指定。生成结果暂存在任务目录，验证通过后发布。发布时原输出目录保留为 `previous-data/`。

中断后用相同命令和任务目录继续。失败批次记录位于任务目录。`--batch-size` 控制每次启动的样本数，`--timeout` 控制单次原生进程的超时秒数。

可用 `--package` 选择一个或多个包型并导出到独立目录。

```powershell
uv run --locked python -m tools.pack_sweep rebuild --package bare_die --package chip_array --output tmp/YYYY-MM-DD-selected-data --work tmp/YYYY-MM-DD-selected-run
```

## 验证与专项核对

```powershell
uv run --locked python -m tools.pack_sweep validate --point flotherm_pack_data/packages/bare_die/baselines/default
uv run --locked python -m tools.pack_reference.activation_audit --root flotherm_pack_data --work tmp/YYYY-MM-DD-activation-audit --output tmp/YYYY-MM-DD-activation-audit/report.json
```

验证包含脚本和 FloXML 的 XSD 校验、DES 回读、案例声明的字段断言及库内基线引用。带 `request` 的点同时比对 PackStudio 模型。单个样本也可用 [FloSCRIPT 工具](../../FLOSCRIPT.md)重放其 `script.xml`。

FC PBGA 激活审计读取专项案例的原生 DES 和 FloXML，核对数据组状态与结构激活机制。
