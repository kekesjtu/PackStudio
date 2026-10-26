# 采用 WebView2 独立宿主

整理日期：2026-10-26。状态：已采用。

## 决策

Windows 独立窗口采用 WPF / .NET 10 与 WebView2，复用浏览器界面和本地 Python 服务。
宿主负责后端启动与退出清理、页面加载、FloXML 原生保存对话框及受限消息通道。
后端通过 PyInstaller 携带运行环境与 JSON 参数库。

## 理由

保持窗口与浏览器模式的建模流程一致，并使用 Windows 原生窗口和文件保存能力。

## 影响与验证

开发机需要 .NET SDK，运行机需要 .NET Desktop Runtime 与 WebView2 Runtime。
宿主只管理自身启动的服务，不接管端口上已有进程。
`tests/webview2/Smoke.cs` 检查实际页面、导出保存、消息和进程生命周期。
打包、启动和验收命令见[开发说明](../development.md)。
