# 默认参数、预设与材料库

运行时只读取本目录 JSON，不需要 FloTHERM 安装、DLL 或 FloXML。

| 路径 | 内容 |
| --- | --- |
| `presets/<family>/<原始名称>.json` | 342 个原生预设、参数状态、未选分支、计算值和原始 DES 字段 |
| `presets/index.json` | 预设族、文件路径、分支及内容 SHA-256 |
| `materials/<分类>/<文件>.json` | 131 个 PACK 内置材料，按十类保存，名称为唯一引用键 |
| `materials/index.json` | 名称、分类、文件路径和 SHA-256 |
| `materials/runtime.json` | 运行材料 ID/颜色映射及空气、界面材料等项目定义；不重复 PACK 物性 |
| `pack_bindings.json` | 当前支持参数和材料组件到原生记录的明确路径 |
| `templates/<PACK 模板 ID>.json` | 界面字段、范围、条件、默认规格及审核等效材料 |
| `request.json` | 当前方案与编辑操作的项目初始设置 |

八种类型按 PACK 顺序为：Chip Array (`chip_array`)、Bare Die (`bare_die`)、Flip Chip CBGA
(`cbga_fc`)、Flip Chip PBGA (`pbga_fc`)、PQFP (`pqfp`)、QFN (`qfn`)、SOP (`sop`)、Wirebond
PBGA (`pbga_wb`)。PQFP 与 SOP 子类型来自原生向导，Footprint 按子类型筛选。
SOP 来源目录仍为 PACK 安装中的 `tsop_conv`，QFN 来源目录为 `QFN`，不改写来源名称。
Bare Die 没有安装目录 DES，保留四个项目审核的尺寸预设。

## 默认值与适配边界

选择预设后读取原生默认分支，按 `pack_bindings.json` 投影已实现字段和材料，再应用用户
显式修改并生成项目等效几何。有效默认值不再用旧 FloXML 基线补全。
例如 Flip Chip PBGA 基板厚度为 1.15 mm；Wirebond PBGA 的两层默认厚度按原生规则取
0.36 或 0.56 mm。完整库还保留 74 个四层分支，界面仍采用当前已实现的两层模型。

原生 `not_applicable` 没有虚构物性或尺寸。未启用散热焊盘的厚度等只保留 `editor_default`，
由用户启用后调整；双侧 QFN 没有 Y 侧引脚。默认值路径和编辑初值范围见
[适配审计](../docs/validation/catalog_presets.json)。未实现的控制项留在完整库，不添加无效开关。

材料随预设按名称解析。常量各向同性和正交各向异性物性直接用于模型。温度依赖材料的
系数、参考温度和原始存储完整保留；当前常量模型采用原生参考温度值并在材料来源中标注。
审核的家族等效张量仍在模板文件中作为基线；键合线、过孔和 PQFP/SOP 承载台在生产阶段按
PACK 保留分支及当前参数/组分重算，见 [联动公式](../docs/research/pack-material-couplings.md)。
组件选材参与组分计算，不把计算后的等效块覆盖为纯金属。完整预设不表示完整几何复刻。

逐球列表仅在原生去球开关启用时生效。部分 Chip Array 名称中的 48/80 与原生启用阵列的
49/81 不一致，界面和审计保留提示，不按文件名猜测去球。

## 复现与检查

提取工具直接读取 DES 和经过 SHA-256 审核的 PACK 2504 原生参数对象，无需 Floscript 导出。
换版本必须重新审核二进制布局，不能绕过版本检查。

```powershell
uv run --locked python -m tools.extract_pack_catalog "E:\Program Files\Siemens\SimcenterFlotherm\2504"
uv run --locked python -m tools.validate_catalog_presets
```

审计位于 `docs/validation/catalog_presets.json`，不进入运行包。旧 `flotherm/` 转录、
`source_adapters.json`、根级 `materials.json`、重复原生快照和旧提取脚本已删除，历史内容通过 Git 查看。
