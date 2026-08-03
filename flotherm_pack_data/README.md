# README

你正在 PackStudio 仓库中执行一次长期、可断点续跑的 Flotherm PACK 参考数据提取任务。

## 一、任务目标

结合 Codex 的 `computer-use` 插件和 Flotherm PACK 的 FloSCRIPT 功能，系统化提取：

1. Flotherm PACK 的封装模板目录。
2. 每个模板的引导式建模流程。
3. 左侧步骤导航、所有参数字段、控件类型、单位、默认值和可选项。
4. 参数之间的显示、启用、互斥和依赖关系。
5. 关键界面状态截图，包括下拉框展开、条件字段启用和模型树状态。
6. 将默认情形、选项开关和参数变化与导出的 FloXML 一一对应，记录选项或参数变化对 FloXML 节点、属性、材料和几何实体的影响。
7. FloXML 中会导出材料定义。将其中的材料属性复制为我们自己的材料库。Bumps + underfill 层存在特殊情况，详见注意事项。

本任务只提取参考资料，不进行过度处理，也不在本任务中直接实现 Flotherm PACK 功能。

## 二、工作范围

- 工作区：`E:\Users\mydearlong\Desktop\PackStudio`
- 提取范围：当前本机 Flotherm PACK 中能够访问的全部封装模板。
- Computer Use 主要负责模板目录扫描、界面流程提取、截图、下拉选项和 Materials Tab 材料属性读取。
- FloSCRIPT 主要负责创建封装、修改参数或选项，以及自动导出 FloXML。

## 三、工作流程

1. 使用 Computer Use 完成模板目录扫描，确认所有需要提取的模板名称。
2. 逐个模板进行默认参数和界面情况提取，并导出默认 FloXML。
3. 每个模板先通过界面完成一次完整的基准操作，从以下目录取得对应的、已经写入完成的 `FlopackLogFile*.xml`：

   `E:\Program Files\Siemens\SimcenterFlotherm\2504\WinXP\bin\LogFiles`

4. 将该日志复制为模板的基准 FloSCRIPT。保留有效的：

   - `new_package`
   - `modify_component`
   - `modify_component_table_row`
   - `export_floxml`

   录制产生的重复选择和中间输入值，只有在确认删除后仍能正常重放时才能清理。

5. 使用以下 XSD 验证每个 FloSCRIPT：

   `E:\Program Files\Siemens\SimcenterFlotherm\2504\examples\FloSCRIPT\Schema\FlopackFloSCRIPTSchema.xsd`

6. 重要的选项开关以基准 FloSCRIPT 为基础，每个脚本只改变一个选项，并导出对应 FloXML。
7. 重要的数值参数以基准 FloSCRIPT 为基础，每个脚本只改变一个参数，并导出对应 FloXML。
8. 每次导出后，将变体 FloXML 与基准 FloXML 比较，记录节点、属性、材料和几何实体的差异。
9. Computer Use 仍负责记录与参数或选项对应的界面截图；FloSCRIPT 中的 `select_component_row` 可以用于打开相应步骤页面。
10. 整理所有 FloXML 中自动导出的材料，再通过 Materials Tab 补充无法从 FloXML 获得的材料属性。
11. 每完成一个截图、FloSCRIPT 执行或 FloXML 导出，都更新 `checkpoint.json`，以便中断后继续。
12. 所有数据仅保存在本地 PackStudio 工作区，不覆盖已经存在的文件。

FloXML 的生成已经由 FloSCRIPT 脚本完成：脚本创建封装、设置单个目标并调用
`export_floxml`。当前只用界面中的 **Play FloSCRIPT** 启动脚本，因为本机 2504
安装未确认存在可靠、受支持的无界面入口，而且任务要求复用用户已打开的同一
PACK 进程。界面不承担逐参数手工导出。

## 四、注意事项

- 本任务是长期、可断点续跑的，需要持续跟踪和维护。
- 不要使用仍在写入、根节点尚未闭合的活动 `FlopackLogFile`。
- 所有选项和参数变体必须从同一模板基准状态生成，每次只改变一个目标变量，避免多个变化混在同一次 FloXML 对比中。
- FloSCRIPT 的 XSD 只规定命令结构，具体的组件名称、参数名称和选项值仍需从实际录制日志中提取，不得自行猜测。
- Flotherm PACK 会直接将 Bumps + underfill 作为一个各向同性的均质材料。因此，存在 Bumps + underfill 层的模型，其最终导出的 FloXML 中不会包含构建等效各向异性层所需的 Bumps 本身和 underfill 材料。
- 对于这种情况，需要在 Flotherm PACK 软件右侧的 Materials Tab 中找到 `C4 Solder Bumps` 和 `Underfill`，并从右下方材料属性栏中分别提取它们的密度、比热和导热系数。
- FloXML 中的 Bumps + underfill 均质材料示例如下：

```xml
<materials>
    <isotropic_material_att>
        <name>Bumps</name>
        <density>1839.5333247093304</density>
        <specific_heat>141.93646049309032</specific_heat>
        <conductivity>6.6548962410187267</conductivity>
    </isotropic_material_att>
</materials>
```

## 五、输出目录结构

```txt
PackStudio/
└── flotherm_pack_data/
    ├── checkpoint.json                     # 全局断点与任务进度状态记录表
    ├── template_catalog.json               # 全部扫描到的封装模板清单与基本信息
    ├── internal_property_registry.json     # UI 字段到 FloSCRIPT 组件/属性的证据化注册表
    ├── parameter_coverage.json             # 扫参策略、分支基线、变体和回放清单
    │
    ├── modeling_option_impacts/            # 重要 option 对建模影响的系统说明
    │   ├── README.md                       # 证据等级、通用公式和 39 项索引
    │   └── NN-<option>.md                  # 一个 UI option 一个文件
    │
    ├── materials/                          # 材料库归档目录
    │   ├── materials_auto_extracted.json   # 从 FloXML 自动导出的材料汇总
    │   ├── materials_manual_captured.json  # 界面 Materials Tab 提取的材料（含 C4 Bumps / Underfill 密度、比热、导热）
    │   └── master_material_library.json    # 最终合并校准的 PackStudio 材料库
    │
    ├── archive/                          # 项目初始化时手动记录的归档目录,无须在意
    ├── validation/                         # 全局生成器、分析器、回放套件及验收证据
    │   ├── comprehensive_replay_*.xml      # 逐模板和全量 FloSCRIPT 回放套件
    │   ├── replay_results.json             # 从 PACK 日志截取的最终回放结果
    │   ├── report.json                     # 全局结构/XSD/FloXML/覆盖率验收报告
    │   └── *.py                            # 注册表提取、脚本生成、差异与材料分析工具
    │
    └── templates/                          # 逐模板提取数据主目录
        └── <Template_ID>/                  # 例如: CBGA、PBGA、PQFP 等
            ├── template.json              # 本模板提取摘要、状态与版本信息
            ├── ui.json                     # 本模板提取的完整左侧 UI 汇总（导航步骤、控件、字段、默认值）
            ├── xml_variations.json         # 本模板提取的选项/参数对 FloXML 的影响汇总
            │
            ├── screenshots/                # 截图保存目录
            │   ├── step_00_template_size.png # 模型可选尺寸截图
            │   ├── step_01_package_substrate.png #右侧建模流程和对应参数选项截图
            │   ├── step_02_die.png
            │   ├── dropdown_XXX.png # 下拉框展开截图
            │   └── model_tree_XXX.png  # 模型树状态
            │
            ├── baseline/                   # 基准默认参数组
            │   ├── params.json             # 基准完整输入参数
            │   ├── script.xml              # 可重放的基准 FloSCRIPT
            │   └── model.xml               # 导出的基准 FloXML 文件
            ├── validation/                 # 基准回放模型与逐模板验收报告
            └── xml_variations/             # FloXML 导出与参数/选项联动验证
                ├── option_switches/        # 开关/选项变化测试组
                │   ├── opt_01_<option_name>/
                │   │   ├── config.json     # 相对于默认变化的选项配置（如：{"中央焊球": True}）
                │   │   ├── model.xml       # 导出的 FloXML
                │   │   ├── script.xml      # 导出的 FloSCRIPT
                │   │   └── diff_xml.json   # 相比 Baseline XML 的节点/属性增减差异分析
                │   └── ...
                │
                └── param_sweeps/           # 数值/参数变化测试组
                    ├── par_01_<param_name>/
                    │   ├── config.json     # 变化的参数（如：{"Substrate_Thickness": 0.3}）
                    │   ├── model.xml       # 导出的 FloXML
                    │   ├── script.xml      # 导出的 FloSCRIPT
                    │   └── diff_xml.json   # 相比 Baseline XML 的数值差异分析
                    └── ...
```

## 六、参数名称、有效值与脚本边界

内部组件名、属性名和有效取值能够直接取得一部分，但当前安装中没有发现一个
可枚举全部字段及约束的权威反射接口。项目按以下证据优先级建立注册表：

1. 实际录制的 FloSCRIPT：组件名、属性名和录制值的最强证据。
2. 每个模板的 `ui.json`：界面可见默认值、选项和值依赖的最强证据。
3. 安装 DLL 的字符串与反汇编映射：补足候选内部名称，但不能单独证明可写。
4. 官方 XSD：只证明 `new_package`、`modify_component`、`export_floxml`
   等命令语法，不列出每个模板的全部组件、属性和合法值。
5. PACK 实际回放与 FloXML 差异：最终确认属性是否可写、值是否被归一化，以及
   是否会改变导出模型。

因此，同一界面标签不能被假设为同一内部属性。例如 Wirebond PBGA 的
`Extent of Bond Wire Pads` 写在 `die.bondWireExtent*`，而 FBGA 的同名字段
写在 `bondWires.extentOfBondWirePads*`。SOIC 的 `overallPackage.lengthD`
虽然可在二进制中找到字符串，但 PACK 2504 在运行时拒绝该写入，注册表将其
明确标记为非独立可扫参数。

FloXML 导出本身完全依靠脚本：生成器创建逐变体 FloSCRIPT，PACK 回放后由
`export_floxml` 写出模型；Computer Use 只负责在现有进程中启动回放和观察
监视器。`validation/` 保存生成器、定向录制/回放证据、逐模板与全量回放套件、
PACK 日志汇总和最终验收报告，不是另一份模板数据。

## 七、提取完成状态

本轮参考数据提取与全面扫参已于 2026-07-29 完成：

- 当前 2504 安装中可访问的 8 个模板均有完整 `ui.json`、关键截图、基准参数、
  基准 FloSCRIPT 和基准 FloXML。`ui_states` 已删除，目录数量经最终验证为 0。
- `internal_property_registry.json` 含 589 个 UI 字段记录，必需属性未解析数为 0。
  名称证据、覆盖策略及运行时排除理由均保留在记录中。
- 扫参不再是旧的“每模板 1 个选项 + 1 个数值”种子集。当前清单覆盖 369 个
  可执行目标、123 个条件分支基线和 656 个单变量变体；每个适用模板的 JEDEC
  取 3 个代表值（含基线），其他选项取全部非默认值，数值取有效低/高值。
- 材料遵循 `default_only`：`No Attachment` 且必须选择非默认材料才能激活的
  分支不会伪造扫参，而是在注册表和覆盖清单中以原因明确记录。
- 788 份生成脚本全部通过官方 FloSCRIPT XSD。最终组合脚本在用户原先打开、
  始终未关闭的同一 PACK 进程中完成 779/779 次导出，错误 0、警告 0。
- 656 个 FloXML 对比中，653 个产生语义变化；3 个是精确列出的默认子状态无
  FloXML 效果（SOIC `dieType=thermalDie` 1 个、`bondWireLengthLbw` 2 个），
  意外无变化为 0。Bond Wire 案例另有界面录制和定向回放证明写入确实被接受。
- 默认材料库只读取 8 份基准 FloXML：62 次材料引用、46 个自动定义、37 个
  不同名称；合并 2 个手工提取的隐藏组分后，主材料库共 48 个定义。
- 8/8 模板、全局数据完整性、脚本 XSD、FloXML 可解析性、回放证据和单变量
  差异检查均已通过，结果见 `validation/report.json`。
- 重要选项的几何增删、材料方向性、联动关系、适用边界和可反算公式已整理到
  [`modeling_option_impacts/`](modeling_option_impacts/README.md)。目录含 39 个语义选项文件，
  覆盖 42 个内部 option 目标；未被 PackStudio 采用的 PACK 分支也保留参考说明并明确标注。

可重复执行的本地验证命令：

```powershell
E:\anaconda\Scripts\conda.exe run -n PackStudio python flotherm_pack_data\validation\analyze_floxml_diffs.py flotherm_pack_data\templates --write-artifacts
E:\anaconda\Scripts\conda.exe run -n PackStudio python flotherm_pack_data\validation\extract_floxml_materials.py flotherm_pack_data
E:\anaconda\Scripts\conda.exe run -n PackStudio python flotherm_pack_data\validation\validate_reference_data.py flotherm_pack_data
```
