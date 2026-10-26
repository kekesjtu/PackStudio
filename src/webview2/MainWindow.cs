using System.IO;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using Microsoft.Web.WebView2.Core;
using BrowserControl = Microsoft.Web.WebView2.Wpf.WebView2;
using Microsoft.Win32;

namespace PackStudio.WebView2;

public sealed class MainWindow : Window
{
  private readonly HostOptions options;
  private readonly BackendSession backend;
  private readonly Func<string, string?> chooseDownloadPath;
  private readonly CancellationTokenSource lifetime = new();
  private readonly TaskCompletionSource ready = new(TaskCreationOptions.RunContinuationsAsynchronously);
  private readonly TextBlock status = new() { Margin = new Thickness(12), Text = "正在准备建模界面…" };
  private bool closing;

  public MainWindow(HostOptions options, Func<string, string?>? chooseDownloadPath = null)
  {
    this.options = options;
    backend = new BackendSession(options);
    this.chooseDownloadPath = chooseDownloadPath ?? SelectDownloadPath;
    Title = "PackStudio · WebView2";
    Width = 1680;
    Height = 960;
    MinWidth = 1024;
    MinHeight = 680;
    WindowStartupLocation = WindowStartupLocation.CenterScreen;
    var layout = new Grid();
    layout.Children.Add(Browser);
    layout.Children.Add(status);
    Content = layout;
    Loaded += async (_, _) => await InitializeAsync();
    Closed += (_, _) =>
    {
      closing = true;
      lifetime.Cancel();
      ready.TrySetCanceled();
      Browser.Dispose();
      backend.Dispose();
      lifetime.Dispose();
    };
    backend.UnexpectedExit += (_, _) => Dispatcher.BeginInvoke(() =>
    {
      if (!closing) ShowError($"建模服务已退出。请重新打开窗口。日志：{backend.LogPath}");
    });
  }

  public BrowserControl Browser { get; } = new() { Visibility = Visibility.Hidden };
  public Task Ready => ready.Task;
  public Uri BackendAddress => backend.Address;

  private async Task InitializeAsync()
  {
    try
    {
      await backend.StartAsync(lifetime.Token);
      var environment = await CoreWebView2Environment.CreateAsync(
          userDataFolder: Path.Combine(options.DataDirectory, "browser"));
      await Browser.EnsureCoreWebView2Async(environment);
      if (closing) return;
      Browser.CoreWebView2.Settings.IsStatusBarEnabled = false;
      Browser.CoreWebView2.NavigationStarting += (_, eventArgs) =>
      {
        if (!IsLocalPage(eventArgs.Uri)) eventArgs.Cancel = true;
      };
      Browser.CoreWebView2.NewWindowRequested += (_, eventArgs) => eventArgs.Handled = true;
      Browser.CoreWebView2.DownloadStarting += SaveDownload;
      Browser.CoreWebView2.WebMessageReceived += ReceiveMessage;
      Browser.CoreWebView2.NavigationCompleted += (_, eventArgs) =>
      {
        if (!eventArgs.IsSuccess)
        {
          var error = new IOException($"页面加载失败：{eventArgs.WebErrorStatus}");
          ShowError(error.Message);
          ready.TrySetException(error);
          return;
        }
        status.Visibility = Visibility.Collapsed;
        Browser.Visibility = Visibility.Visible;
        ready.TrySetResult();
      };
      Browser.Source = backend.Address;
    }
    catch (Exception error)
    {
      if (closing) return;
      backend.Dispose();
      ShowError($"{error.Message}\n日志：{backend.LogPath}");
      ready.TrySetException(error);
    }
  }

  private bool IsLocalPage(string address)
  {
    if (address.StartsWith("blob:", StringComparison.Ordinal)) address = address[5..];
    return Uri.TryCreate(address, UriKind.Absolute, out var uri)
        && uri.GetLeftPart(UriPartial.Authority) == backend.Address.GetLeftPart(UriPartial.Authority);
  }

  private void ReceiveMessage(object? sender, CoreWebView2WebMessageReceivedEventArgs eventArgs)
  {
    if (!IsLocalPage(eventArgs.Source)) return;
    try
    {
      using var message = JsonDocument.Parse(eventArgs.WebMessageAsJson);
      var payload = message.RootElement;
      if (payload.GetProperty("type").GetString() != "packstudio-ping") return;
      Browser.CoreWebView2.PostWebMessageAsJson(JsonSerializer.Serialize(new
      {
        type = "packstudio-pong",
        protocol_version = "packstudio.host/v1",
        request_id = payload.GetProperty("request_id").GetString(),
      }));
    }
    catch (Exception error) when (error is JsonException or KeyNotFoundException or InvalidOperationException)
    {
      // Unrecognized messages cannot invoke native host operations.
    }
  }

  private void SaveDownload(object? sender, CoreWebView2DownloadStartingEventArgs eventArgs)
  {
    var deferral = eventArgs.GetDeferral();
    eventArgs.Handled = true;
    // A native modal must open after the WebView2 event returns to its message loop.
    Dispatcher.BeginInvoke(() =>
    {
      try
      {
        if (closing) { eventArgs.Cancel = true; return; }
        var path = chooseDownloadPath(Path.GetFileName(eventArgs.ResultFilePath));
        if (path is not null) eventArgs.ResultFilePath = path;
        else eventArgs.Cancel = true;
      }
      finally { deferral.Complete(); }
    });
  }

  private string? SelectDownloadPath(string filename)
  {
    var dialog = new SaveFileDialog
    {
      FileName = filename,
      Filter = "FloXML 模型 (*.floxml)|*.floxml",
      DefaultExt = ".floxml",
      AddExtension = true,
    };
    return dialog.ShowDialog(this) == true ? dialog.FileName : null;
  }

  private void ShowError(string message)
  {
    Browser.Visibility = Visibility.Hidden;
    status.Text = message;
    status.TextWrapping = TextWrapping.Wrap;
    status.Visibility = Visibility.Visible;
  }
}
