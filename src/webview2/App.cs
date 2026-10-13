using System.Windows;

namespace PackStudio.WebView2;

public static class App
{
  [STAThread]
  public static int Main(string[] args)
  {
    try
    {
      var options = HostOptions.Parse(args);
      var application = new Application();
      return application.Run(new MainWindow(options));
    }
    catch (Exception error)
    {
      MessageBox.Show(error.Message, "PackStudio 启动失败", MessageBoxButton.OK,
          MessageBoxImage.Error);
      return 1;
    }
  }
}
