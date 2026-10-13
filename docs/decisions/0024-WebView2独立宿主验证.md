# ADR-0024：WebView2 独立宿主验证

日期：2026-10-13。状态：已实施，用户已授权移除 Electron。

## 背景

用户希望 PackStudio 未来成为 PTA 中的一个建模模块，并要求先尝试独立 WebView2 窗口。
本机 PTA 安装依赖表明其使用 WPF / .NET 10；本机具备 .NET 10 SDK 与 WebView2 Runtime。
现有 React 界面和 Python 领域规则已分离，不需要为改变窗口壳重写建模逻辑。

## 决策

- 新增 src/webview2 下的 WPF 宿主，目标 net10.0-windows，锁定 WebView2 NuGet 版本。
- 使用现有生产前端，由 FastAPI 同源托管；不运行 Vite 开发服务器。
- 开发模式通过 uv 启动锁定的后端；分发模式使用完整 PyInstaller onedir 产物。
- 默认使用固定 18080 端口，便于同一浏览器配置下恢复参数；冲突时明确报错。
  自动端口作为显式选项，更换端口的 localStorage 不作为同一个项目的参数记录。
- 使用 Windows Job Object 管理自己启动的后端及子进程，正常关闭和强制退出均清理。
- PTA XML / ECXML 的 Blob 下载接入原生 SaveFileDialog，通过 WebView2 deferral 延后打开模态窗口。
- 仅接收同源页面的限定消息，提供 ping/pong 往返以验证原生通道，不提供任意宿主对象调用。
- 独立宿主验证通过后，根据用户授权删除 Electron 壳、依赖、NSIS 配置和专用测试。
  默认 desktop、package:desktop、dist 和 test:desktop 命令切换到 WebView2。

## 验证与交付边界

实际 WebView2 验证程序检查 React 页面、WebGL 上下文、八类模型生成与 PTA XML 导出、
Blob 下载保存为有效 PTA XML、宿主消息回执、端口冲突不影响已有监听、
正常关闭和强制终止后的后端清理。
源码模式与运行目录模式分别验证，运行目录包含 Python 与默认参数库。
原生窗口检查覆盖四栏界面、三维预览、导出对话框与取消返回。
用户按 Escape 停止后已停止 Computer Use；原生对话框最终点击保存未继续手动操作，
文件落盘由注入保存路径的自动化下载测试验证。

运行目录为框架依赖发布，需 .NET Desktop Runtime 10 和 WebView2 Runtime；
当前不包含这两个运行时的安装器，也未在没有这些运行时的机器上验证。
尚未实现 PTA 模型加载、应用回执及项目参数回存；后续取得 PTA 源码后接入。
当前进程启动与网页 API 仅为本机独立原型；宿主会话鉴权与项目上下文协议随 PTA 集成实现。

## 后续交付完善

在常用机器、显卡、DPI 和远程桌面场景完成验证，并确定安装/升级方案后，
继续完善 Windows 安装器、运行时分发、升级及 PTA 模型加载。
当前 WebView2 已是 Windows 桌面默认入口，React、Python 与现有 XML 导出器继续复用。

官方依据：
[WPF WebView2](https://learn.microsoft.com/en-us/microsoft-edge/webview2/get-started/wpf)、
[宿主消息](https://learn.microsoft.com/en-us/microsoft-edge/webview2/how-to/communicate-btwn-web-native)、
[线程与模态窗口](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/threading-model)。
