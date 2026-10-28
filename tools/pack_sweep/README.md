# PACK 原生扫参与参考库

在仓库根目录通过 uv 运行。需要已安装并可运行的 Flotherm PACK；安装位置可用
`--installation` 指定，默认位置见 [FloSCRIPT 本机操作](../../FLOSCRIPT.md)。

## 完整重建

先归档整个参考目录，再执行重建。归档名和任务目录请使用本次任务的日期与名称：

```powershell
uv run --locked python -m tools.pack_sweep archive --archive flotherm_pack_data_archives/2026-10-28-full.zip
uv run --locked python -m tools.pack_sweep rebuild --snapshot flotherm_pack_data_archives/2026-10-28-full.zip --work tmp/2026-10-28-pack-sweep
uv run --locked python -m tools.pack_sweep validate
```

归档包括隐藏文件、临时资料和空目录，逐文件核对 SHA-256，旁边保存完整清单。
重建在任务目录内调用 PACK，生成全新 XML 和 DES，通过验证后发布到输出目录。
发布前再次检查原目录与归档一致，避免覆盖归档后的编辑。
`flotherm_pack_data/` 纳入版本控制；完整归档与任务临时目录仅本地保存。
参考数据使用原始字节入库，Git 不转换其换行，以保持原生导出与文件指纹一致。

中断后使用相同命令与任务目录继续：已有点必须输入一致且通过重新验证；
失败批次的运行记录保留在任务目录。修改扫参定义后应使用新的任务目录。
`--batch-size` 控制每次启动的点数，`--timeout` 控制单次原生进程超时秒数。

仅导出指定模板到独立目录时，可重复传入 `--template`：

```powershell
uv run --locked python -m tools.pack_sweep rebuild --template bare_die --template chip_array --output tmp/2026-10-28-selected-data --work tmp/2026-10-28-selected-run
```

## 目录与验证

```text
flotherm_pack_data/
  index.json
  verification.json
  screenshots.json
  template/<template>/
    index.json
    screenshots/
    <point>/
      case.json
      script.xml
      model.xml
      model.des
      input.des          # 仅 DES 附件/参数探针需要
      native_run.json
      verification.json
```

`script.xml` 使用点目录内的相对路径，可交给 `tools.floscript run` 再次执行。
原生版本、二进制哈希、批次脚本哈希和点文件哈希保存在 `native_run.json`。
通过统一命令验证整个参考库或指定扫参点：

```powershell
uv run --locked python -m tools.pack_sweep validate
uv run --locked python -m tools.pack_sweep validate --point flotherm_pack_data/template/bare_die/baseline
```

验证包含输入脚本 XSD、FloXML XSD、DES 回读和文件指纹。
带 `request` 的点还与 PackStudio 生成结果比对几何、材料、温度依赖材料律、
功率、监测点和网格；差异政策仅来自 `docs/decisions/`。
参考库保留产品范围外的原生扫参点。其原生 FloXML 若不符合 schema，报告明确记为
`native_schema_error`，汇总为 `passed_with_native_schema_errors`，不视作 schema 通过。
带产品请求的案例遇到此类错误直接中止重建。

## 维护入口

- `specs/<template>.json`：声明式扫参输入，含基线、单参数变化及比较基线。
- `cases/`：产品请求与原生指令的对应案例、预设矩阵、DES 附件及金属层探针。
- `inputs.py`：八类模板共享的 XML 构造入口。
- `rebuild.py`：批量执行、断点恢复与验证后发布。
- `compare.py`、`decisions.py`：公共模型比对与项目决策规则。
- `archive.py`、`screenshots.py`：完整归档和截图保留。
- [tools/floscript](../floscript/)：底层 schema、DES、原生隔离运行环境和隐藏进程启动。

新增点须有稳定名称、可重复的输入与可解释的验证范围。运行产物不写入工具目录。
