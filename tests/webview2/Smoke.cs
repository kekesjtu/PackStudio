using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Text.Json;
using System.Windows;
using System.Xml.Linq;
using Microsoft.Web.WebView2.Core;
using PackStudio.WebView2;

namespace PackStudio.WebView2Smoke;

public static class Smoke
{
  [STAThread]
  public static int Main(string[] args)
  {
    var root = Path.GetFullPath(args.Length > 0 ? args[0] : Environment.CurrentDirectory);
    var data = Path.Combine(root, "tmp", "webview2-smoke", Guid.NewGuid().ToString("N"));
    var application = new Application { ShutdownMode = ShutdownMode.OnExplicitShutdown };
    var window = new MainWindow(new HostOptions(root, 0, data), filename => Path.Combine(data, filename));
    window.Loaded += async (_, _) =>
    {
      try
      {
        await window.Ready.WaitAsync(TimeSpan.FromSeconds(55));
        await CheckPortConflictAsync(root, data);
        await WaitForPageAsync(window);
        await CheckBrowserApiAsync(window);
        await CheckDownloadAsync(window, data);
        Directory.CreateDirectory(data);
        await using (var image = File.Create(Path.Combine(data, "preview.png")))
          await window.Browser.CoreWebView2.CapturePreviewAsync(
                  CoreWebView2CapturePreviewImageFormat.Png, image);
        var address = window.BackendAddress;
        window.Close();
        using var client = new HttpClient(new HttpClientHandler { UseProxy = false });
        try
        {
          await client.GetAsync(new Uri(address, "api/health"));
          throw new InvalidOperationException("窗口关闭后后端仍然存活。");
        }
        catch (HttpRequestException) { }
        await CheckForceCloseAsync(root, data);
        Console.WriteLine($"PASS: WebView2 页面、WebGL、八类生成/导出、XML 文件保存、宿主消息、端口冲突、退出清理。截图：{data}");
        application.Shutdown(0);
      }
      catch (Exception error)
      {
        Console.Error.WriteLine(error);
        if (window.IsLoaded && window.Browser.CoreWebView2 is not null)
        {
          Console.Error.WriteLine(await window.Browser.ExecuteScriptAsync("document.body.innerText.slice(0, 600)"));
          await using var image = File.Create(Path.Combine(data, "failure.png"));
          await window.Browser.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, image);
          Console.Error.WriteLine($"失败截图：{data}");
        }
        window.Close();
        application.Shutdown(1);
      }
    };
    return application.Run(window);
  }

  private static async Task CheckDownloadAsync(MainWindow window, string data)
  {
    await window.Browser.ExecuteScriptAsync("""
      [...document.querySelectorAll('button')].find(button => button.textContent === '导出 PTA XML').click();
      """);
    var path = Path.Combine(data, "cbga_fc.xml");
    for (var attempt = 0; attempt < 100; attempt++)
    {
      if (File.Exists(path) && new FileInfo(path).Length > 0)
      {
        try
        {
          var root = XDocument.Load(path).Root;
          if (root?.Name.LocalName == "Structure") return;
        }
        catch (IOException) { }
        catch (System.Xml.XmlException) { }
      }
      await Task.Delay(100);
    }
    throw new InvalidOperationException("浏览器 Blob 下载未通过宿主保存为有效 PTA XML。");
  }

  private static async Task CheckForceCloseAsync(string root, string data)
  {
    var listener = new TcpListener(IPAddress.Loopback, 0);
    listener.Start();
    var port = ((IPEndPoint)listener.LocalEndpoint).Port;
    listener.Stop();
    var packagedHost = Path.Combine(root, "PackStudio.WebView2.exe");
    var executable = File.Exists(packagedHost) ? packagedHost : Path.Combine(root,
        "build", "dotnet", "PackStudio.WebView2", "bin", "Release", "net10.0-windows", "PackStudio.WebView2.exe");
    var start = new ProcessStartInfo(executable) { UseShellExecute = false, CreateNoWindow = true };
    foreach (var argument in new[] { "--root", root, "--port", port.ToString(),
                     "--data-dir", Path.Combine(data, "force-close") }) start.ArgumentList.Add(argument);
    using var process = Process.Start(start) ?? throw new IOException("强制退出测试启动失败。");
    using var client = new HttpClient(new HttpClientHandler { UseProxy = false })
    { Timeout = TimeSpan.FromSeconds(1) };
    var address = $"http://127.0.0.1:{port}/api/health";
    try
    {
      var started = false;
      for (var attempt = 0; attempt < 100; attempt++)
      {
        if (process.HasExited) throw new IOException("强制退出测试的宿主提前退出。");
        try
        {
          using var response = await client.GetAsync(address);
          if (response.IsSuccessStatusCode) { started = true; break; }
        }
        catch (HttpRequestException) { }
        catch (TaskCanceledException) { }
        await Task.Delay(100);
      }
      if (!started) throw new TimeoutException("强制退出测试的后端未启动。");
      process.Kill(entireProcessTree: false);
      await process.WaitForExitAsync();
      await Task.Delay(300);
      client.Dispose();
      for (var attempt = 0; attempt < 30; attempt++)
      {
        var probe = new TcpListener(IPAddress.Loopback, port);
        try
        {
          probe.Server.ExclusiveAddressUse = true;
          probe.Start();
          return;
        }
        catch (SocketException) { }
        finally { probe.Stop(); }
        await Task.Delay(100);
      }
      throw new InvalidOperationException("宿主被强制终止后留下了后端进程。");
    }
    finally { if (!process.HasExited) process.Kill(entireProcessTree: true); }
  }

  private static async Task CheckPortConflictAsync(string root, string data)
  {
    var listener = new TcpListener(IPAddress.Loopback, 0);
    listener.Start();
    try
    {
      var port = ((IPEndPoint)listener.LocalEndpoint).Port;
      using var session = new BackendSession(new HostOptions(root, port, Path.Combine(data, "conflict")));
      try
      {
        await session.StartAsync(CancellationToken.None);
        throw new InvalidOperationException("占用端口不应被当作 PackStudio 服务复用。");
      }
      catch (IOException error) when (error.Message.Contains("已被占用")) { }
      if (!listener.Server.IsBound) throw new InvalidOperationException("用户已有监听被关闭。");
    }
    finally { listener.Stop(); }
  }

  private static async Task WaitForPageAsync(MainWindow window)
  {
    for (var attempt = 0; attempt < 100; attempt++)
    {
      var result = await window.Browser.ExecuteScriptAsync("""
                (() => {
                  const canvas = document.querySelector('canvas');
                  const gl = canvas?.getContext('webgl2');
                  return document.querySelector('.template-workspace') !== null &&
                    [...document.querySelectorAll('button')].some(b => b.textContent === '生成模型' && !b.disabled) &&
                    gl !== null && gl !== undefined && !gl.isContextLost() && gl.drawingBufferWidth > 0;
                })()
                """);
      if (result == "true") return;
      await Task.Delay(200);
    }
    throw new InvalidOperationException("参数界面或 WebGL 未完成渲染。");
  }

  private static async Task CheckBrowserApiAsync(MainWindow window)
  {
    await window.Browser.ExecuteScriptAsync("""
            window.__probe = null;
            (async () => {
              const get = async path => {
                const response = await fetch(path);
                if (!response.ok) throw new Error(`${path}: ${response.status}`);
                return response.json();
              };
              const catalog = await get('/api/templates');
              if (catalog.length !== 8) throw new Error('模板数量错误');
              const results = [];
              for (const {id} of catalog) {
                const parameters = await get(`/api/templates/${id}/defaults`);
                const post = path => fetch(path, {
                  method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(parameters),
                });
                const generated = await post(`/api/templates/${id}/generate`);
                if (!generated.ok) throw new Error(`${id} 生成失败`);
                const model = await generated.json();
                const exported = await post(`/api/templates/${id}/export/pta`);
                const xml = new DOMParser().parseFromString(await exported.text(), 'application/xml');
                if (!exported.ok || xml.documentElement.localName !== 'Structure' || !model.blocks.length)
                  throw new Error(`${id} 导出失败`);
                results.push({id, blocks: model.blocks.length});
              }
              const reply = await new Promise((resolve, reject) => {
                const timer = setTimeout(() => reject(new Error('宿主消息超时')), 3000);
                const listener = event => {
                  if (event.data.type !== 'packstudio-pong') return;
                  clearTimeout(timer);
                  window.chrome.webview.removeEventListener('message', listener);
                  resolve(event.data);
                };
                window.chrome.webview.addEventListener('message', listener);
                window.chrome.webview.postMessage({type: 'packstudio-ping', request_id: 'smoke'});
              });
              if (reply.request_id !== 'smoke') throw new Error('宿主消息标识错误');
              window.__probe = {ok: true, results, reply};
            })().catch(error => { window.__probe = {ok: false, error: String(error)}; });
            """);
    for (var attempt = 0; attempt < 200; attempt++)
    {
      var result = await window.Browser.ExecuteScriptAsync("window.__probe");
      if (result != "null")
      {
        using var payload = JsonDocument.Parse(result);
        if (!payload.RootElement.GetProperty("ok").GetBoolean())
          throw new InvalidOperationException(result);
        Console.WriteLine(result);
        return;
      }
      await Task.Delay(200);
    }
    throw new TimeoutException("浏览器内模型接口检查超时。");
  }
}
