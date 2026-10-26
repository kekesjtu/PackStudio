# ADR-0029：BGA 与 Bumps 建模表达

日期：2026-10-26。状态：决策已确认，bumps 实现待对齐。

## 项目决策

- BGA 焊球保留离散和等效两种表达。
- Bumps 建模选项只实现有厚度的 Isotropic Cuboid 等效层。
- 不提供 Collapse Cuboid 选项。

## 实现状态

文档整理时，现有 bumps 生成代码仍使用正交各向异性等效层，与本决策的
Isotropic Cuboid 要求存在差距。本次不修改其等效公式，也不将其标记为已完成。
后续实现需要先核对原生 Isotropic Cuboid 的物性规则及适用分支，再更新代码和测试。

本决策不规定焊球布局、交错阵列、Solder Ball Map 或通孔的功能取舍。

## 依据

用户指定的外部《功能取舍.md》第 2 节。按当前原文保留 Isotropic Cuboid，
不沿用旧记录中的 Orthotropic 表述；理由未在来源中记录。
来源位置见[决策索引](README.md)。
