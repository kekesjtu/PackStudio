# TASK21 — 修复 Footprint 与顶盖分支前端联动

状态：已完成。日期：2026-10-12。

- [x] 切换 Footprint 保留独立顶盖选择、功率、用户选材及 BGA 表达方式，重置关联尺寸。
- [x] 分支切换清理隐藏/禁用字段覆盖与不活动的材料绑定。
- [x] 恢复旧保存方案时清理相同残留，避免初次生成失败。
- [x] 真实 CBGA/PBGA schema 前端回归与后端 fixture 一致性检查。
- [x] 四个真实 UI 转移请求通过实际后端生成；30项前端、47项相关后端测试通过。
- [x] lint、ruff、前端构建及提交说明完成。

修复验证：[pack_frontend_fixes.json](../validation/pack_frontend_fixes.json)。
提交说明：[2026-10-12_前端规格与顶盖联动修复](../git_commits/2026-10-12_前端规格与顶盖联动修复.md)。
