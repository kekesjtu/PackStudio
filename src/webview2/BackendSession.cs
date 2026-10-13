using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Text.Json;

namespace PackStudio.WebView2;

public sealed class BackendSession : IDisposable
{
  private readonly HostOptions options;
  private readonly HttpClient client = new(new HttpClientHandler { UseProxy = false })
  { Timeout = TimeSpan.FromSeconds(30) };
  private Process? process;
  private OwnedProcessJob? job;
  private bool disposed;

  public BackendSession(HostOptions options) => this.options = options;
  public Uri Address { get; private set; } = null!;
  public string LogPath => Path.Combine(options.DataDirectory, "backend.log");
  public event EventHandler? UnexpectedExit;

  public async Task StartAsync(CancellationToken cancellationToken)
  {
    Directory.CreateDirectory(options.DataDirectory);
    File.WriteAllText(LogPath, $"{DateTimeOffset.Now:O} 正在启动 PackStudio 后端。{Environment.NewLine}");
    var packaged = File.Exists(Path.Combine(options.Root, "backend", "packstudio-backend.exe"));
    var frontend = Path.Combine(options.Root, packaged ? "frontend" : "dist");
    if (!File.Exists(Path.Combine(frontend, "index.html")))
      throw new FileNotFoundException("缺少前端构建，请先运行 npm run build。", frontend);
    var listener = new TcpListener(IPAddress.Loopback, options.Port);
    try
    {
      listener.Start();
      Address = new Uri($"http://127.0.0.1:{((IPEndPoint)listener.LocalEndpoint).Port}/");
    }
    catch (SocketException error)
    {
      throw new IOException($"端口 {options.Port} 已被占用，请关闭旧窗口或指定其他端口。", error);
    }
    finally { listener.Stop(); }

    var start = new ProcessStartInfo
    {
      FileName = packaged ? Path.Combine(options.Root, "backend", "packstudio-backend.exe") : "uv",
      WorkingDirectory = options.Root,
      UseShellExecute = false,
      CreateNoWindow = true,
      RedirectStandardError = true,
      RedirectStandardOutput = true,
    };
    if (!packaged)
    {
      foreach (var argument in new[] { "run", "--locked", "--no-sync", "--no-dev", "python", "-m", "packstudio" })
        start.ArgumentList.Add(argument);
    }
    start.ArgumentList.Add("--port");
    start.ArgumentList.Add(Address.Port.ToString());
    start.Environment["PACKSTUDIO_FRONTEND_DIR"] = frontend;
    process = new Process { StartInfo = start, EnableRaisingEvents = true };
    process.OutputDataReceived += (_, eventArgs) => Log(eventArgs.Data);
    process.ErrorDataReceived += (_, eventArgs) => Log(eventArgs.Data);
    process.Exited += (_, _) => { if (!disposed) UnexpectedExit?.Invoke(this, EventArgs.Empty); };
    try
    {
      job = new OwnedProcessJob();
      process.Start();
      job.Assign(process);
      process.BeginOutputReadLine();
      process.BeginErrorReadLine();
      using var deadline = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
      deadline.CancelAfter(TimeSpan.FromSeconds(45));
      await WaitForHealthAsync(deadline.Token);
      foreach (var path in new[] { "api/templates", "api/templates/materials",
                         "api/templates/cbga_fc/schema", "api/templates/cbga_fc/defaults" })
      {
        using var response = await client.GetAsync(new Uri(Address, path), deadline.Token);
        response.EnsureSuccessStatusCode();
      }
    }
    catch
    {
      Dispose();
      throw;
    }
  }

  private async Task WaitForHealthAsync(CancellationToken cancellationToken)
  {
    while (true)
    {
      cancellationToken.ThrowIfCancellationRequested();
      if (process!.HasExited)
        throw new IOException($"后端启动失败，请查看日志：{LogPath}");
      try
      {
        using var response = await client.GetAsync(new Uri(Address, "api/health"), cancellationToken);
        response.EnsureSuccessStatusCode();
        using var payload = JsonDocument.Parse(await response.Content.ReadAsStringAsync(cancellationToken));
        if (payload.RootElement.GetProperty("service").GetString() != "packstudio")
          throw new IOException("端口上的服务不是 PackStudio。");
        return;
      }
      catch (HttpRequestException) { }
      catch (TaskCanceledException) when (!cancellationToken.IsCancellationRequested) { }
      await Task.Delay(150, cancellationToken);
    }
  }

  private void Log(string? message)
  {
    if (message is null) return;
    lock (client)
    {
      try
      {
        File.AppendAllText(LogPath, $"{DateTimeOffset.Now:O} {message}{Environment.NewLine}");
      }
      catch (IOException) { }
      catch (UnauthorizedAccessException) { }
    }
  }

  public void Dispose()
  {
    if (disposed) return;
    disposed = true;
    job?.Dispose();
    if (process is not null)
    {
      try
      {
        if (!process.HasExited) process.Kill(entireProcessTree: true);
        process.WaitForExit(3000);
      }
      catch (InvalidOperationException) { }
      process.Dispose();
    }
    client.Dispose();
  }
}
