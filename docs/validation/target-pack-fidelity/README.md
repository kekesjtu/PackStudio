# Bare Die、FC 与 Chip Array 原生对照

## 实现范围

| 模板 | 建模规则 |
| --- | --- |
| Bare Die | Si/GaAs 材料、翻转标记、带凸点芯片的高度、均匀体热源、局部网格与结温监测点 |
| Flip Chip CBGA/PBGA | 规则/非规则凸点计数、底填开关、四种顶部结构、齐平塑封、加强环、散热块与支脚粘接 |
| Flip Chip PBGA | 芯层金属表、离散/正交通孔、显式去孔、独立上下增层与微通孔等效 |
| Chip Array | 两层/四层初始化、可编辑金属层表、顶层中央材料区、Accurate/Approximate 通孔、填孔、键合线开关与计数 |
| 三类 BGA | 棋盘式 Staggered、外围满布行列、显式名单优先级、独立中央阵列、CSV 球位图、离散/等效表达 |

Bumps 使用[各向同性等效层](../../decisions/BGA与Bumps建模表达.md)。
Bare Die 的原生凸点采用正交物性；对照按此决策验证厚度、轴向导热率、密度与比热。
Chip Array 的等效焊球使用 BGA 公共等效规则。
芯片热源使用[均匀体热源](../../decisions/仅支持均匀芯片热源.md)。
原生重叠块遵循[重叠块与警告](../../decisions/重叠块与警告.md)。

## 球位与计数

显式名单的坐标为 `(column, row)`，第 0 行在正 Y 侧；规则网格与交错筛选使用
居中网格坐标。中央加球是独立阵列，保留重合球。
Chip Array 的通孔跟随主阵列，不跟随中央加球和 CSV 球位图。
自动键合线数量在 CSV 分支取表格条目数；其他分支采用主阵列行列数与外围满布行列公式，
显式去球及 Staggered 对该公式的线数没有影响。

FC PBGA 正交通孔在各向同性基板分支保留原生的零基体导热率行为；
密度和比热仍使用所选基板物性。金属表 Depth 从整个基板顶面量起。

## 证据与验证

`evidence.zip` 包含 93 个原生案例的输入、FloSCRIPT、DES 回读、FloXML、
程序版本、二进制哈希和运行检查结果。`advanced-run.json` 覆盖显式名单与 CSV 附件。
证据通过本机 PACK 2025.13.1.1142、FloSCRIPT XSD 和 FloXML XSD 验证。

回归测试从公共生成接口生成模型并导出 FloXML，逐块比较坐标、尺寸、数量及物性，
检查网格约束、总功率与导出 XSD。案例覆盖奇偶边框、填充率大于一、重复球位、
空 CSV、材料联动、上下增层、微通孔和散热块支脚。

```powershell
uv run --locked python -m tools.pack_fidelity --output tmp/target-pack-run --archive docs/validation/target-pack-fidelity/evidence.zip
uv run --locked pytest tests/backend/templates/test_target_pack_fidelity.py
uv run --locked python -m tools.validate_catalog_presets
```
