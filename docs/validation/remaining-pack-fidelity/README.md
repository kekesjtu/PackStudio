# PQFP、QFN、SOP 与 Wirebond PBGA 原生对照

## 建模范围

| 模板 | 建模规则 |
| --- | --- |
| PQFP | 四侧引线框、内部自定义覆盖率、键合线分侧取整、有效线长、短竖段省略、方向物性、八条连接筋、裸露焊盘初始化、散热焊盘及焊料 |
| SOP | 独立承载台金属与厚度、共用承载台等效材料的两条连接筋、连续芯片胶层堆叠、双侧引线框、四侧键合线、只读名义路径 |
| QFN | 逐根或正交等效引脚及焊料、DAP、分段键合线及逐段等效材料、离散或 Lumped 通孔、固定孔间基体、可选板侧散热焊盘 |
| Wirebond PBGA | 两层/四层初始化、六槽位金属表、逐层覆盖率与通孔断开区、承载台覆盖率、离散/正交/各向同性通孔、键合线方向物性、背面扩散片、散热块及支脚粘接 |

四类模板支持原生局部网格约束及温度监测点。
Wirebond PBGA 的焊球与其他 BGA 模板共用阵列、交错、外围满布行列、
独立中央阵列、显式名单及 CSV 球位图规则；BGA 等效表达采用正交物性。
原生重叠块保留在模型、预览与导出中，并参与重叠警告检测。

QFP 承载台与连接筋采用引线框金属。SOP 承载台独立选材，连接筋共用承载台覆盖率物性。
QFN 的分段水平块跨度按段数等分，横向包络从芯片宽度线性变化到引脚阵列跨度，
每段材料按本段包络计算线体积分数，竖段使用末段物性。
QFN Lumped 通孔的内部背景物性为 0.32 W/(m·K)、1200 kg/m³、880 J/(kg·K)。

WB 内层铜与通孔断开区共用纵向公式 `z = 基板顶面 − Depth − 层厚`，
顶面由 Depth 决定，层厚从该顶面向下展开。通孔断开区的
平面范围为通孔原始阵列跨度加两侧各一个孔径。

## 决策对应

- QFP 的连接筋实体采用 Accurate，几何与导出范围遵循[连接筋板范围](../../decisions/QFP连接筋板输出范围.md)。
- SOP 的芯片与胶层遵循[连续堆叠规则](../../decisions/原生bug-SOP芯片与胶层堆叠.md)。
- SOP 的键合线参数遵循[只读名义路径规则](../../decisions/原生bug-SOP键合线线长参数.md)。
- WB 通孔端点遵循[外层铜内表面接触规则](../../decisions/原生bug-Wirebond-PBGA通孔纵向位置.md)。
- WB 内层铜遵循[Depth 与自身厚度定位规则](../../decisions/原生bug-Wirebond-PBGA内层铜纵向位置.md)，与对应断开区对齐。
- 芯片热源采用均匀体热源；材料组和缺省材料遵循[组件选材决策](../../decisions/材料组与默认材料.md)。

## 证据与验收

`evidence.zip` 包含本机 PACK 2025.13.1.1142 的 277 组原生输入、FloSCRIPT、DES、
FloXML、程序指纹及 XSD 验证结果，覆盖四类全部 210 个预设和 67 个基线/变参案例。
案例覆盖不同芯片长宽、线数取整、正负零高差、独立承载台厚度、材料选择、
自定义覆盖率、分段、两层/四层、不等铜厚、通孔表达、扩散片和散热块支脚。

回归通过公共生成与导出接口逐块比较坐标、尺寸、数量、三向导热率、密度和比热，
并比较原生网格约束、监测点、区域、局部网格开关及总功率。
项目决策差异在独立测试辅助模块中按原生组件坐标校正；源证据保留原值。

```powershell
uv run --locked python -m tools.remaining_fidelity --output tmp/remaining-native --archive docs/validation/remaining-pack-fidelity/evidence.zip
uv run --locked pytest tests/backend/templates/test_remaining_pack_fidelity.py
uv run --locked python -m tools.validate_catalog_presets
```
