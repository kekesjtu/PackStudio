# PTA 技术栈与原生桌面架构

## 目标

PackStudio 前端与后端统一采用本机 PTA 的技术栈，面向 Windows 原生桌面使用。参数向导、材料编辑、模型检查与文件导出无需本地 HTTP 服务。

## 架构约束

- C# / .NET 10；WPF 界面，CommunityToolkit.Mvvm 组织状态与命令。
- HelixToolkit.Wpf 提供矩形块三维预览，Fluent.Ribbon 提供功能区，AvalonDock 提供工作区布局。
- 领域核心通过类型化数据与方法供界面和命令行复用，Newtonsoft.Json 读取运行库与方案，NLog 记录桌面日志。
- 生产应用只依赖 .NET 桌面技术栈；Python 与 uv 用于独立的原生研究和参考数据维护。
- JSON 运行数据与 FloXML XSD 是可分发资源，不依赖本机 PTA、Flotherm PACK 或参考归档。
- 保留八类封装、材料等效规则、均匀芯片热源、模型树和 FloXML 接口契约。

## 技术栈参照

本机 PTA 安装清单声明 .NET 10，CommunityToolkit.Mvvm 8.3.2、HelixToolkit.Wpf 3.1.2、Fluent.Ribbon 9.0.4、Dirkster.AvalonDock 5.0.0、Newtonsoft.Json 13.0.3 与 NLog 4.5.10。使用的第三方运行依赖与参照保持同版本，通过 NuGet 锁文件固定。