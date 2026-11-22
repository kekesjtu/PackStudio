using System.IO;
using System.IO.Pipes;
using System.Text;
using System.Text.Json;

namespace PackStudio.Desktop;

internal static class PtaSession
{
    const int ProtocolVersion = 1;
    static readonly JsonSerializerOptions Json = new(JsonSerializerDefaults.Web);

    public static Guid? Parse(string[] args)
    {
        if (args.Length == 0)
            return null;
        if (args is ["--pta-session", var value] && Guid.TryParseExact(value, "N", out Guid id) && id != Guid.Empty)
            return id;
        throw new ArgumentException("启动参数应为 --pta-session <由 32 个十六进制字符组成的会话 ID>。");
    }

    public static async Task SendAsync(Guid sessionId, string projectPath)
    {
        using var pipe = new NamedPipeClientStream(".", $"PackStudio.PTA.{sessionId:N}", PipeDirection.InOut,
            PipeOptions.Asynchronous | PipeOptions.CurrentUserOnly);
        try
        {
            await pipe.ConnectAsync(5_000);
        }
        catch (TimeoutException)
        {
            throw new IOException("PTA 会话未连接，请从 PTA 重新启动 PackStudio。");
        }

        using var responseTimeout = new CancellationTokenSource(TimeSpan.FromMinutes(2));
        using var reader = new StreamReader(pipe, Encoding.UTF8, leaveOpen: true);
        Reply? reply;
        try
        {
            byte[] request = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(new Transfer(ProtocolVersion, projectPath), Json) + "\n");
            await pipe.WriteAsync(request, responseTimeout.Token);
            string line = await reader.ReadLineAsync(responseTimeout.Token)
                ?? throw new IOException("PTA 已结束会话，工程打开结果未确认。");
            reply = JsonSerializer.Deserialize<Reply>(line, Json);
        }
        catch (OperationCanceledException) when (responseTimeout.IsCancellationRequested)
        {
            throw new IOException("等待 PTA 确认打开工程超时，请查看 PTA 窗口。");
        }
        catch (JsonException ex)
        {
            throw new IOException("PTA 返回的工程打开结果格式无效。", ex);
        }

        if (reply?.Version != ProtocolVersion || reply.Opened is null)
            throw new IOException("PTA 返回的工程打开结果与当前协议不匹配。");
        if (reply.Opened == false)
            throw new IOException(string.IsNullOrWhiteSpace(reply.Message) ? "PTA 未打开工程。" : reply.Message);
    }

    sealed record Transfer(int Version, string ProjectPath);
    sealed record Reply(int Version, bool? Opened, string? Message);
}
