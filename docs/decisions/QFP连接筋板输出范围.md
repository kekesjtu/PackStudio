# QFP 连接筋板输出范围

## 决策

QFP 不建模、不输出 `tiebar_plt`。

## 依据与范围

依据为用户明确确认的 QFP 几何与输出范围，适用模板为 `pqfp`。
本项约定针对连接筋板 `tiebar_plt`；连接筋实体的建模选项见
[QFP Tie Bars 建模选项](QFP连接筋建模选项.md)。

## 实现对照

`pqfp_tie_bar_drafts` 生成四角八条连接筋，使用连接筋等效材料。
向导的组件选材与 FloXML 导出采用同一组连接筋实体。
