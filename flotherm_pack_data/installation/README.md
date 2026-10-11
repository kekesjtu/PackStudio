# 安装目录来源证据

`presets.json` 保存 PACK 2504 的 342 个原始 DES 文本、空值、相对路径和原文件 SHA-256。
它仅用于开发期来源核对，不参与运行或打包。

完整原生默认值已迁到 `default_parameters/presets/`，材料迁到分类 `default_parameters/materials/`。
重复原生聚合快照与旧提取工具已删除。复现入口：
`uv run --locked python -m tools.extract_pack_catalog <安装目录>`。

早期背景见 [文本预设调研](../../docs/research/flotherm-installation-defaults.md) 和
[原生默认值调研](../../docs/research/flotherm-native-defaults.md)。历史脚本和快照通过 Git 查看；
当前机制见 [默认参数库说明](../../default_parameters/README.md)。
