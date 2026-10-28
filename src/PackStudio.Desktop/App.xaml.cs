using System.Windows;
using NLog;

namespace PackStudio.Desktop;
public partial class App : Application
{
    public static string DataRoot => System.IO.Path.Combine(AppContext.BaseDirectory, "runtime_data");

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        var config = new NLog.Config.LoggingConfiguration();
        var file = new NLog.Targets.FileTarget("file")
        {
            FileName = System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "PackStudio", "logs", "desktop.log"),
            ArchiveAboveSize = 2 * 1024 * 1024,
            MaxArchiveFiles = 3
        };
        config.AddRule(LogLevel.Info, LogLevel.Fatal, file);
        LogManager.Configuration = config;
        DispatcherUnhandledException += (_, args) =>
        {
            LogManager.GetCurrentClassLogger().Error(args.Exception);
            MessageBox.Show(args.Exception.Message, "PackStudio", MessageBoxButton.OK, MessageBoxImage.Error);
            args.Handled = true;
        };
        try
        {
            var window = new MainWindow();
            MainWindow = window;
            window.Show();
        }
        catch (Exception ex)
        {
            LogManager.GetCurrentClassLogger().Error(ex);
            MessageBox.Show(ex.Message, "PackStudio 启动失败");
            Shutdown(1);
        }
    }

    protected override void OnExit(ExitEventArgs e)
    {
        LogManager.Shutdown();
        base.OnExit(e);
    }
}
