# 文档路由

`docs/` 目录的索引，按主题指向具体文档。

## 需求与架构

| 入口 | 内容 |
| --- | --- |
| [requirements.md](requirements.md) | 产品宏观功能与范围：八类封装、材料、模型树、输出定位 |
| [architecture.md](architecture.md) | 进程内架构、创建到导出的数据流、模块职责与校验边界 |

## 决策

用户拍板的业务目标、技术取舍与交互约束，按主题分目录。

| 主题 | 决策 |
| --- | --- |
| 预设与方案 | [预设来源与空值](decisions/projects/预设来源与空值.md) · [方案文件与模型输出](decisions/projects/方案文件与模型输出.md) · [方案创建与分支配置](decisions/projects/方案创建与分支配置.md) |
| 产品范围与输出 | [封装与传热范围](decisions/projects/封装与传热范围.md) · [仅保留 PackStudio XML 输出](decisions/projects/仅保留PackStudioXML输出.md) |
| 封装建模 | [BGA 与 Bumps 建模表达](decisions/modeling/BGA与Bumps建模表达.md) · [FC 顶盖与均热板粘接层](decisions/modeling/FC顶盖与均热板粘接层.md) · [QFP 连接筋](decisions/modeling/QFP连接筋.md) · [重叠块与警告](decisions/modeling/重叠块与警告.md) |
| 创建与参数编辑 | [新建封装与向导导航](decisions/desktop/新建封装与向导导航.md) · [数值输入框交互](decisions/desktop/数值输入框交互.md) · [去球与去孔矩阵选择](decisions/desktop/去球与去孔矩阵选择.md) · [封装示意图](decisions/desktop/封装示意图.md) |
| 工作区与模型检查 | [工作区与三维操作](decisions/desktop/工作区与三维操作.md) · [模型树排序与显隐](decisions/desktop/模型树排序与显隐.md) |
| 材料 | [材料组与默认材料](decisions/materials/材料组与默认材料.md) · [材料物性可信度提示](decisions/materials/材料物性可信度提示.md) |
| 与 PACK 原生模型的差异 | [FC 顶盖侧壁与芯片重叠](decisions/native-bugs/原生bug-FC顶盖侧壁与芯片重叠.md) · [FC PBGA 通孔](decisions/native-bugs/原生bug-FC-PBGA通孔等效基体导热率.md) · [FC Slug 支脚与胶层](decisions/native-bugs/原生bug-FC-Slug支脚与胶层纵向位置.md) · [Wirebond PBGA 通孔](decisions/native-bugs/原生bug-Wirebond-PBGA通孔纵向位置.md) · [Wirebond PBGA 内层铜](decisions/native-bugs/原生bug-Wirebond-PBGA内层铜纵向位置.md) · [SOP 堆叠](decisions/native-bugs/原生bug-SOP芯片与胶层堆叠.md) · [SOP 键合线](decisions/native-bugs/原生bug-SOP键合线线长参数.md) |

## 参考

| 入口 | 内容 |
| --- | --- |
| [DES字段与内部参数对应表.md](DES字段与内部参数对应表.md) | 内部字段、原生 DES 与 PACK 属性的对照（人工核对） |
| [DES字段与内部参数对应表.json](DES字段与内部参数对应表.json) | 上述对照的机器可读版本 |
