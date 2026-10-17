# ADR25 — FloXML 导出与物理差异验证

日期：2026-10-17；状态：采用。

## 导出决策

FloXML 为独立导出器，不复用 ECXML 标签。契约为本机 FloTHERM 2504
`WinXP/PlugIns/XML_PLUGIN_SCHEMA` 的五份原始 XSD，以及 PACK 原生导出。
XSD 随开发契约保存，生产请求不读取安装、XSD、参考目录或研究资料。

直接输出当前 PackageModel：每个无重叠块一个 SI `cuboid`，每组一个零位移
`assembly`，材料以唯一 ID 绑定。导热张量使用常量 isotropic/orthotropic；
密度和比热保留当前值，不为了兼容 PACK 静默改写模型。

`HeatSource` 表示块内体源。同块功率累加为一个 total `source_att` 和无材料、
无 occupancy、无 collapse 的 `source` 几何。它不增加实体体积、质量或热容量。
PACK 常用 collapsed 面源；两者功率可比较，空间分布不能宣称等价。
面边界和网格参数只在 notes 保留审计值，界面提示目标软件重新配置。

## 验证决策

分别比较原始 builder cuboid 与最终导出物理分区。独立验证器累积 assembly 位移，
统一为 mm；匹配几何后记录原生路径、项目 ID、结构角色、材料及优先级。
名称不作为几何/物性相等的条件。

PACK 原始体存在重叠，不能直接求和。对照分区采用已匹配的项目优先级，使用独立
差集实现计算体积、质量和热容量；这不是 FloTHERM 求解器重叠优先级的反向证明。
原生 collapsed 实体只做名义包络分析，明确标为 provisional。
未知旋转、材料模型或物理几何报错，不自动猜测。控制 region/monitor 单独登记。

差异归入功能取舍、具有物理依据的不同实现、已确认缺陷、原生继承风险、证据不足
五类。已有建模缺陷在报告中呈现，独立于新增导出器保真验收，不在本任务中全部改写。
相同数字、XML 可解析、测试通过均不等于模型已获热仿真精度验证。
