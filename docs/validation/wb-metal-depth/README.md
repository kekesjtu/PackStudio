# Wirebond PBGA 内层铜深度对照

`evidence.zip` 保存本机 PACK 2025.13.1.1142 的六组独立输入、原生 DES 回读、
FloSCRIPT、FloXML、版本、哈希和 XSD 检查结果。
原生输入固定基板底面 0.60 mm、基板厚度 0.56 mm，
分别改变顶铜厚度、内层厚度和内层 Depth，并启用该内层的 Disconnect to Via。

实验确认原生内层铜底面依赖两倍顶铜厚度，断开区顶面按 Depth 定位。
两者偏差及修复范围见[内层铜纵向位置决策](../../decisions/原生bug-Wirebond-PBGA内层铜纵向位置.md)。
源证据保留原生坐标；生产模型按该决策使内层铜与对应断开区对齐。

回归在离散、正交及各向同性通孔模式下，将内层铜及断开区的端面与原生断开区对照，
并验证 FloXML 坐标、厚度、XSD、输入回读及源文件指纹。

```powershell
uv run --locked pytest tests/backend/templates/test_wirebond_metal_depth.py
```
