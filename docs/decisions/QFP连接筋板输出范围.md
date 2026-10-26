# QFP 连接筋板输出范围

## 决策

QFP 不建模、不输出 `tiebar_plt`。

## 依据与范围

依据为用户明确确认的 QFP 几何与输出范围，适用模板为 `pqfp`。
本项约定针对连接筋板 `tiebar_plt`；连接筋实体的建模选项见
[QFP Tie Bars 建模选项](QFP连接筋建模选项.md)。

## 实现对照

`pqfp_tie_bar_drafts` 包含 `tie-bar-plate-*` 物理块，所属组件为 `group-tie-bar-plates`。
FloXML 导出器消费生成模型中的物理块，该生成逻辑与本决策的几何及输出范围存在实现差距。
