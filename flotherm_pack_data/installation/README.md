# 安装目录证据快照

`presets.json` 来自本机 Simcenter FloTHERM 2504 的 342 个 PACK `.des` 文本预设。
保存相对来源、原文件 SHA-256、原始字段/空值，以及 25 个当前生产预设的匹配记录。
21 个非 Bare Die 预设的 42 个芯片 X/Y 值全部匹配。

复现脚本为 `tools/research_flotherm_installation.py`；来源、范围和局限见
[调研报告](../../docs/research/flotherm-installation-defaults.md)。
这里不参与生产运行或打包，不把空串当作数值零。

2026-10-11 增加直接读取 PACK DLL 初始化结果的快照：

- `native_defaults.json`：342 个默认向导分支。
- `native_defaults_4layer.json`：74 个四层基板分支。
- `native_defaults_audit.json`：来源核对、条件规则、六份归档 FloXML 核对和生产差异。

入口为 `uv run --locked python -m tools.extract_pack_native_defaults`，无需 FloSCRIPT 或
新导出 FloXML。范围、版本限制、复现命令及完备性边界见
[原生默认值调研](../../docs/research/flotherm-native-defaults.md)。
这些研究快照尚未接入生产默认值；对 WB 的三个字段已发现 56 处生产差异。
