# TASK19：原生预设适配、PACK 全链路命名与清理

状态：已完成（代码与验收，清理权限限制见下）；日期：2026-10-11。

- [x] 八种 Package Types 名称与顺序和 PACK 对齐。
- [x] API、字段、Python 模块、JSON 文件、模型和下载文件统一 ID，不保留旧别名。
- [x] PQFP、SOP 子类型和 Footprint 联动，后端校验组合。
- [x] 有效默认值直接读取完整原生库，选材按名称解析独立分类库。
- [x] 删除旧转录、缺值继承、重复快照和被替代工具。
- [x] 保存空间升级，不恢复旧方案；归档对照采用显式历史输入。
- [x] 完成后端、前端、桌面与导出验收。
- [x] 提交说明和变更一同提交。

边界：完整原生库保留已提取分支，运行时投影当前支持几何。温度依赖材料按原生参考温度
投影为常量物性，在来源和参数库文档中明确记录。

清理限制：旧预设、重复快照、被替代工具和可访问临时产物已删除。Windows 拒绝访问
`tmp/pytest-source-1`、`tmp/pytest-source-full-1`、`tmp/pytest-source-full-final`、
`tmp/pytest-source-pin-final`、`tmp/pytest-source-portable-final` 及 `.pytest_cache`；
所有权修复未成功，保留为未跟踪残留，需要拥有者或管理员清理，不影响运行和提交。
