# 输出格式

桌面端在“导出 XML”中选择格式。CLI 的 `generate` 根据输出文件名识别 `.pta.xml`。

| 文件 | 用途 |
| --- | --- |
| [PackStudio XML](packstudio/README.md)（`.packstudio.xml`） | 下游网格与求解模块的模型接口，按米描述几何，按瓦描述块功率。 |
| [PTA 工程示例](pta/bare-die.pta.xml)（`.pta.xml`） | PTA 3.1.0 / 3.2.1 工程格式，使用根级独立块、矩形阵列和布尔差集，几何单位为毫米，体积功率密度为 W/m³。 |

仓库内由 PackStudio 导出的 PTA 样例统一放在 `pta/`，包括[带焊球和通孔的 BGA](pta/BGA-焊球与通孔.pta.xml)。外部[格式说明与原始样例](PTA-工程文件/工程文件格式说明.md)保存在 `PTA-工程文件/`。

PTA 工程采用三维稳态固体传热、FDM 和 300 K 环境温度与初始温度。材料导热率写为常量。温度相关材料取参考温度下的导热率，各向异性材料按 X、Y、Z 顺序写三个分量。边界条件由使用者在 PTA 中设置，网格线与求解结果由 PTA 生成。

## PTA 会话交接

PTA 为每次启动生成新的非空 GUID，按 `N` 格式传入 `PackStudio.exe --pta-session <id>`，并监听本地双向字节模式命名管道 `PackStudio.PTA.<id>`。管道名使用小写 GUID。两进程使用同一 Windows 用户及提升权限级别，服务端使用 `PipeOptions.CurrentUserOnly | PipeOptions.Asynchronous`。

安装后，PTA 可从 `HKLM\Software\Microsoft\Windows\CurrentVersion\App Paths\PackStudio.exe` 的默认值读取桌面程序路径。

PackStudio 显示「传回 PTA」并导出独立工程。每次传输用一个连接，双方使用 UTF-8、无 BOM、以换行结束的一行 JSON。请求包含协议版本和已写完的 `.pta.xml` 绝对路径。

```json
{"version":1,"projectPath":"C:\\Projects\\die.pta.xml"}
```

发起会话的 PTA 打开该工程后回复 `{"version":1,"opened":true}`。取消或失败时回复 `{"version":1,"opened":false,"message":"打开失败的原因"}`。PTA 可在断开本次连接后继续监听同一会话，以接收后续按键交接。PackStudio 等待连接最多 5 秒，连接后等待回复最多 2 分钟。只有收到成功回复才显示已打开，交接失败时显示已导出的文件路径。

直接启动 PackStudio 时，按钮为「在 PTA 中打开」，通过 `PTA.exe` 的工程路径参数打开独立工程。

[floxml/](floxml/README.md)中的厂商 XSD 和示例只供原生 PACK 研究工具使用，不随产品分发。
