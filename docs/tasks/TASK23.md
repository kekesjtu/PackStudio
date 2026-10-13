# TASK23 — 独立 WebView2 宿主验证

状态：已完成。日期：2026-10-13。

- [x] 核实本机 .NET 10 SDK 和 WebView2 Runtime。
- [x] 新增 WPF / WebView2 窗口，复用现有 React 页面与 Python 后端。
- [x] 实现就绪预热、启动错误、限定来源消息及原生导出保存对话框。
- [x] 实现默认固定端口与显式自动端口，冲突不接管用户已有服务。
- [x] 使用 Windows Job Object 清理自身后端及子进程。
- [x] 源码和打包模式均完成 WebGL、八类生成/导出、消息、端口冲突及退出验证。
- [x] 生成独立运行目录，不需要 uv、Node 或独立 Python 环境。
- [x] 更新使用文档、ADR 和提交说明，随代码提交。
- [x] 根据用户授权移除 Electron 实现、依赖、打包配置和测试，默认桌面入口改为 WebView2。

本任务验证独立窗口，不包含 PTA 自动导入或现有项目合并。
运行目录仍依赖 .NET Desktop Runtime 10 与 WebView2 Runtime。

记录：[ADR-0024](../decisions/0024-WebView2独立宿主验证.md)。
