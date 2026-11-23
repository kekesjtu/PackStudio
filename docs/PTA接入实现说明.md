# PTA 接入 PackStudio 实现说明

PTA 的「封装模板」按钮启动 PackStudio。用户完成建模后，在 PackStudio 点「传回 PTA」，发起会话的 PTA 窗口打开导出的 `.pta.xml` 独立工程并返回结果。两个应用独立安装。工程文件由 PackStudio 导出，PTA 使用自身的工程打开流程处理。首版的交接单位是完整的独立工程。

## 1. 定位并启动 PackStudio

1. 读取 64 位注册表视图中 `HKLM\Software\Microsoft\Windows\CurrentVersion\App Paths\PackStudio.exe` 的默认值。这个值是安装后的 `PackStudio.exe` 完整路径。若值缺失或已失效，允许用户选择发布目录中的 `PackStudio.exe`，并在 PTA 设置中记住该路径。使用前检查路径是绝对路径、指向 `PackStudio.exe` 且文件存在。 [Windows App Paths](https://learn.microsoft.com/en-us/windows/win32/shell/app-registration)
2. 每次启动生成新的非空 GUID，按 `N` 格式转换为 **32 个小写十六进制字符**。先创建本机命名管道服务端，再启动 PackStudio。传入两个独立参数 `--pta-session` 和会话 ID。用 `ProcessStartInfo.ArgumentList` 逐项传参，程序路径放在 `FileName` 中，工作目录设为可执行文件所在目录。
3. 管道绑定到发起按钮的 PTA 窗口。PackStudio 与 PTA 在同一 Windows 用户和权限提升级别下运行。启动失败时结束该会话，并在 PTA 里提示用户检查 PackStudio 路径。 [PipeOptions](https://learn.microsoft.com/dotnet/api/system.io.pipes.pipeoptions)

启动示例中的 ID 由 PTA 为本次启动生成，并同时用于管道名。

```text
"C:\Program Files\PackStudio\PackStudio.exe" --pta-session 6b1b2e2c80d746658f9179073a0ed9ea
```

## 2. 接收工程并回复

| 项目 | 协议 v1 |
| --- | --- |
| 服务端 | 发起会话的 PTA 窗口，管道名 `PackStudio.PTA.<id>`，本机双向字节模式，`PipeOptions.Asynchronous \| PipeOptions.CurrentUserOnly` |
| 消息边界 | 每次交接建立一个连接，收一行请求，回一行结果。双方使用 UTF-8、无 BOM，每行以 `\n` 结束 |
| 请求 | `version` 为整数 `1`。`projectPath` 为已写完的 `.pta.xml` 文件绝对路径 |
| 回执 | `version` 为整数 `1`，`opened` 为布尔值。失败或取消时 `opened` 为 `false`，`message` 为面向用户的原因 |
| 等待时间 | PackStudio 最多等待连接 5 秒，连接后最多等待回复 2 分钟。允许用户保存确认和工程加载占用这段时间 |
| 生命周期 | 一次连接处理一个工程。收发完成后可以继续监听同一会话，接收后续点击。发起 PTA 窗口关闭或对应的 PackStudio 进程退出时结束会话 |

请求、成功回执和失败回执分别如下。实际传输时，每个 JSON 对象各占一行。

```json
{"version":1,"projectPath":"C:\\Users\\User\\AppData\\Local\\PackStudio\\PTA\\Projects\\裸芯片.pta.xml"}
```

```json
{"version":1,"opened":true}
```

```json
{"version":1,"opened":false,"message":"已取消打开，当前工程保留。"}
```

PTA 收到请求后，校验协议版本、路径和文件是否存在，然后将打开操作调度到发起窗口的 UI 线程。复用 PTA「打开工程」的未保存修改确认及读入流程，直接传入工程路径即可跳过文件选择。仅在该窗口完成工程加载和状态更新后返回 `opened: true`。用户取消、保存失败或工程读取失败时，保留当前工程并返回 `opened: false`。管道断开或回复超时只表示 PackStudio 未收到确认，PTA 应保留实际打开结果，不自动再次打开或回滚。导出的文件继续留在原路径，供重试或手动打开。 [WPF UI 线程调度](https://learn.microsoft.com/dotnet/desktop/wpf/advanced/threading-model)

## 3. C# 接入参考

以下代码面向 Windows 上的 .NET 10。`RunAsync` 是一次按钮启动会话的入口。PTA 窗口负责提供已验证的程序路径、工程打开回调和窗口关闭令牌，并异步等待此方法。窗口关闭时取消等待即可，PackStudio 仍可继续编辑自己的方案。

```csharp
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

internal static class PackStudioSession
{
    private const int ProtocolVersion = 1;
    private static readonly JsonSerializerOptions Json = new(JsonSerializerDefaults.Web);

    internal static async Task RunAsync(
        string packStudioExe,
        Func<string, CancellationToken, Task<(bool Opened, string? Message)>> openProjectAsync,
        Action<Exception> logError,
        CancellationToken windowClosed)
    {
        windowClosed.ThrowIfCancellationRequested();
        string sessionId = Guid.NewGuid().ToString("N");
        using var pipe = new NamedPipeServerStream(
            $"PackStudio.PTA.{sessionId}", PipeDirection.InOut, 1, PipeTransmissionMode.Byte,
            PipeOptions.Asynchronous | PipeOptions.CurrentUserOnly);
        using var lifetime = CancellationTokenSource.CreateLinkedTokenSource(windowClosed);

        var startInfo = new ProcessStartInfo(packStudioExe)
        {
            WorkingDirectory = Path.GetDirectoryName(packStudioExe)!,
            UseShellExecute = false
        };
        startInfo.ArgumentList.Add("--pta-session");
        startInfo.ArgumentList.Add(sessionId);
        using var process = Process.Start(startInfo)
            ?? throw new InvalidOperationException("无法启动 PackStudio。");

        Task listen = ServeAsync(pipe, openProjectAsync, logError, lifetime.Token);
        Task processExited = process.WaitForExitAsync(lifetime.Token);
        await Task.WhenAny(listen, processExited).ConfigureAwait(false);
        lifetime.Cancel();
        try
        {
            await Task.WhenAll(listen, processExited).ConfigureAwait(false);
        }
        catch (OperationCanceledException) when (lifetime.IsCancellationRequested)
        {
        }
    }

    private static async Task ServeAsync(
        NamedPipeServerStream pipe,
        Func<string, CancellationToken, Task<(bool Opened, string? Message)>> openProjectAsync,
        Action<Exception> logError,
        CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            await pipe.WaitForConnectionAsync(cancellationToken).ConfigureAwait(false);
            try
            {
                using var reader = new StreamReader(pipe, Encoding.UTF8, leaveOpen: true);
                using var requestTimeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
                requestTimeout.CancelAfter(TimeSpan.FromSeconds(10));
                string? line = await reader.ReadLineAsync(requestTimeout.Token).ConfigureAwait(false);
                if (line is null)
                    continue;

                Reply reply = await OpenAsync(line, openProjectAsync, logError, cancellationToken)
                    .ConfigureAwait(false);
                byte[] payload = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(reply, Json) + "\n");
                using var replyTimeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
                replyTimeout.CancelAfter(TimeSpan.FromSeconds(10));
                await pipe.WriteAsync(payload, replyTimeout.Token).ConfigureAwait(false);

                // PackStudio 读完回执后关闭连接，等到 EOF 再断开，避免丢弃未读回执。
                await reader.ReadAsync(new char[1].AsMemory(), replyTimeout.Token).ConfigureAwait(false);
            }
            catch (IOException ex)
            {
                logError(ex);
            }
            catch (OperationCanceledException ex) when (!cancellationToken.IsCancellationRequested)
            {
                logError(ex);
            }
            finally
            {
                pipe.Disconnect();
            }
        }
    }

    private static async Task<Reply> OpenAsync(
        string line,
        Func<string, CancellationToken, Task<(bool Opened, string? Message)>> openProjectAsync,
        Action<Exception> logError,
        CancellationToken cancellationToken)
    {
        Request? request;
        try
        {
            request = JsonSerializer.Deserialize<Request>(line, Json);
        }
        catch (JsonException)
        {
            return new(ProtocolVersion, false, "无法读取 PackStudio 的交接请求。");
        }

        if (request?.Version != ProtocolVersion)
            return new(ProtocolVersion, false, "PTA 不支持此交接协议版本。");
        if (request.ProjectPath is not { } path || !Path.IsPathFullyQualified(path)
            || !path.EndsWith(".pta.xml", StringComparison.OrdinalIgnoreCase) || !File.Exists(path))
            return new(ProtocolVersion, false, "找不到有效的 PTA 工程文件。");

        try
        {
            var result = await openProjectAsync(path, cancellationToken).ConfigureAwait(false);
            return new(ProtocolVersion, result.Opened, result.Message);
        }
        catch (Exception ex) when (!cancellationToken.IsCancellationRequested)
        {
            logError(ex);
            return new(ProtocolVersion, false, "PTA 无法打开工程，请查看 PTA 日志。");
        }
    }

    private sealed record Request(int Version, string? ProjectPath);
    private sealed record Reply(int Version, bool Opened, string? Message);
}
```

在 PTA 的 WPF 窗口中，把回调接到实际的工程打开方法。下面的 `TryOpenProjectFromPath` 由 PTA 提供，返回 `(bool Opened, string? Message)`。若现有加载流程在读取前会清空窗口，应先读取和校验目标工程，再提交到当前窗口。按钮事件中等待 `RunAsync`，处理进程启动和管道异常。每个窗口可在会话期间禁用「封装模板」按钮，避免同一窗口同时打开多个待接收工程。`windowClosedToken` 随发起窗口关闭而取消，日志回调应可在后台线程调用。

```csharp
await PackStudioSession.RunAsync(
    packStudioExe,
    (path, token) => Dispatcher.InvokeAsync(
        () => TryOpenProjectFromPath(path), DispatcherPriority.Normal, token).Task,
    LogPackStudioError,
    windowClosedToken);
```

参考实现收到回执读取完成后的连接关闭信号，再释放当前连接。Windows 断开命名管道时会丢弃尚未读走的数据。 [DisconnectNamedPipe](https://learn.microsoft.com/windows/win32/api/namedpipeapi/nf-namedpipeapi-disconnectnamedpipe)

## 4. 联调验收

| 场景 | 应观察到的结果 |
| --- | --- |
| 安装路径含空格或中文 | PTA 通过注册表或手动选择的路径启动 PackStudio，会话参数解析成功 |
| 从 PTA 发起并正常传回 | PackStudio 显示「传回 PTA」。发起窗口打开独立块工程，PackStudio 收到成功回执 |
| 当前 PTA 工程有未保存改动，用户取消打开 | 当前工程保持原状，PackStudio 显示取消原因和已导出路径 |
| 工程文件不存在或无法读取 | PTA 回复失败原因，PackStudio 保留导出路径供排查 |
| 两个 PTA 窗口分别发起 | 各自收到对应会话的工程，关闭其中一个窗口不会影响另一会话 |
| 发起的 PTA 窗口在传回前关闭 | PackStudio 提示会话未连接并显示已导出文件路径 |
| 关闭 PackStudio，或同一会话再次交接 | 进程退出后 PTA 释放会话。同一运行中的 PackStudio 可以再次传回，仍由发起窗口处理 |
| 从桌面直接启动 PackStudio | 按钮为「在 PTA 中打开」，使用 PTA 的工程路径启动入口 |

工程 XML 的建模语义和样例见 [输出格式](../output_format/README.md)。
