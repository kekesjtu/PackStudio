# WebView2 独立宿主

## 决策

Windows 独立窗口采用 WPF / .NET 10 与 WebView2，复用浏览器界面和本地 Python 服务。
宿主负责后端启动与退出清理、页面加载、FloXML 原生保存对话框及受限消息通道。
后端通过 PyInstaller 携带运行环境与 JSON 参数库。

## 依据

独立窗口与浏览器模式共享建模流程，并使用 Windows 原生窗口和文件保存能力。

## 运行与验证

开发机使用 .NET SDK，运行机使用 .NET Desktop Runtime 与 WebView2 Runtime。
宿主管理自身启动的服务进程，并通过端口检查报告占用情况。
`tests/webview2/Smoke.cs` 检查页面、导出保存、宿主消息与进程生命周期。
打包、启动和验收命令见[开发说明](../development.md)。
