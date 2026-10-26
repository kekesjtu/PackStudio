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
通用原生导出入口见根目录 [FloSCRIPT 本机操作说明](../../FLOSCRIPT.md)。
一次性原生实验工具已冻结归档到本机 `flotherm_pack_data/archive/legacy-tools-20261026.zip`，
不再作为当前维护入口。历史实验数据和其中的脚本快照保持原貌。
回归测试仍需使用的比较模块保留在 `tools/floxml_validation/`；
原生目录、材料与参数辅助模块集中在 `tools/pack_reference/`。
