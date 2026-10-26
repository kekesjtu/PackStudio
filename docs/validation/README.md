# 验证数据与测试夹具

本目录保留项目回归所需的原生导出证据、审计输入指纹和历史结果。
这些文件描述各自验证时点，不定义当前需求或已批准的 PACK 功能取舍。
历史数据中的旧文档路径保留原貌，可通过 Git 历史追溯。
原 `catalog_presets.json` 含停用格式的检查结果，完整原件已收入
[参考归档](../../archive/README.md)；当前同名报告由 FloXML 审计工具实际重跑生成。

## 测试直接读取的数据

| 数据 | 使用位置 |
| --- | --- |
| `floxml/evidence.zip` | `tests/backend/test_floxml_comparison.py`、`tests/backend/templates/test_leadframe_model_fixes.py` |
| `catalog_presets.json` | `tests/backend/templates/test_source_presets.py`，检查预设覆盖、输入哈希、几何引用和 FloXML XSD 结果 |

其他报告、原生实验 JSON 和证据压缩包继续保留。移动或删除前必须核对测试与工具引用。
更新报告需要实际运行对应验证，不把旧结果改写成新一轮通过记录。

## 当前验证入口

```powershell
uv run --locked pytest
uv run --locked python -m tools.validate_catalog_presets
```

后一个命令重新生成 342 个源预设的适配审计，当前只检查 FloXML 导出。
PACK 原生实验的复现工具仍在 `tools/`，通常需要本机安装和本地参考数据。
