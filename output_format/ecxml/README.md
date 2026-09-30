# ECXML 格式契约

此目录保存 ECXML 1.0 契约与 PackStudio 示例。附件
[ECXML File Format](../../docs/ECXML%20File%20Format.pdf) 中的 Block (Box)、Material、
Mesh Region 示例用于核对结构；[Ansys 官方格式说明](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v242/en/Subsystems/Icepak/Content/Variables/ECXMLFileFormat.htm)
也说明仅交换轴对齐几何，并支持各向异性材料。

## 文件来源

- `ECXML.xsd`：从本机 Simcenter FloTHERM 2504 的
  `WinXP/PlugIns/ECXML_PLUGIN_SCHEMA/ECXML.xsd` 原样复制。
- 原始 SHA-256：`3a9913e9ac99297aa8013772a15eb15726fed0016637ede28f6bfb32fa977603`。
- `bare-die.ecxml`：由当前 Bare Die 默认参数生成的可复现示例。
- XSD 只用于开发期验证，不作为软件运行时依赖。

## 映射

| 内部模型 | ECXML 表达 |
| --- | --- |
| 模型名 | `neutralXML/name` |
| 组件组及父子关系 | `geometry/assembly`，递归嵌套 |
| 物理矩形块 | `solid3dBlock`，无布尔压缩、层切片或重复源块 |
| origin、size（mm） | `location`、`size`（m），乘以 0.001，坐标轴与原点不变 |
| 材料 ID | material `name` 与块 `material`，名称保存在审计注释 |
| kx=ky=kz | `thermalConductivity/isotropic/conductivity`，W/(m·K) |
| 其他三向 k | `thermalConductivity/orthotropic/x,y,z`，W/(m·K) |
| 密度、比热 | `density`（kg/m³）、`specific_heat`（J/(kg·K)） |
| 块体热源 | 累加为 `powerDissipation`（W），有热源的实体仍为材料块 |

PACK 的矩形等效空气填充区域也以保留其物性的材料块输出；这不定义 CFD 流体域。
没有生成 `solutionDomain`，封装包络不被误用为 CFD 计算区域。

## 格式限制

XSD 的 `producer` 仅接受 `FloTHERM` 或 `Icepak`。PackStudio 选择 `FloTHERM` 兼容配置，
XML 注释明确记录实际导出者为 PackStudio；此字段不代表文件由 Siemens 软件生成。
领域材料没有发射率参数，因此 `surfaceEmissivity=0`，不引入辐射模型。

ECXML 没有通用的逐面温度/热流/换热条件或 PTA 最大网格尺寸字段。原始边界、环境和
网格预设保存在 `PackStudio export metadata` JSON 注释中供审计；目标软件不会自动应用。
界面显示格式限制，下载响应包含 `X-PackStudio-Export-Warnings`。
需要完整边界与网格预设时使用 PTA XML；ECXML 导入后应在目标软件中配置这些控制。

API：`POST /api/templates/{template_id}/export/ecxml`，请求与模型生成接口相同，
文件名为 `<template-id>.ecxml`。
[Ansys ImportECXML 示例](https://ansyshelp.ansys.com/public/Views/Secured/Electronics/v242/en/Subsystems/Icepak/Subsystems/Icepak%20Scripting/Content/ImportECXML.htm)
使用 `.ecxml` 扩展名。

## 验证

```powershell
uv run --locked pytest tests/backend/exporters/test_ecxml.py
```

测试按安装 XSD 校验八类模板，并逐块验证 SI 坐标、材料、层级和功率；还覆盖离散 BGA、
自定义三向材料、多源累加、中文/XML 字符转义和下载接口。
XSD 校验及数值核对已通过；FloTHERM / Icepak 内实际导入仍属于下游人工验收。
