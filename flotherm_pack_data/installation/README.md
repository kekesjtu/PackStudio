# 安装目录证据快照

`presets.json` 来自本机 Simcenter FloTHERM 2504 的 342 个 PACK `.des` 文本预设。
保存相对来源、原文件 SHA-256、原始字段/空值，以及 25 个当前生产预设的匹配记录。
21 个非 Bare Die 预设的 42 个芯片 X/Y 值全部匹配。

复现脚本为 `tools/research_flotherm_installation.py`；来源、范围和局限见
[调研报告](../../docs/research/flotherm-installation-defaults.md)。
这里不参与生产运行或打包，不把空串当作数值零。
