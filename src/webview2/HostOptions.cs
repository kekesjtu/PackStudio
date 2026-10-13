using System.IO;

namespace PackStudio.WebView2;

public sealed record HostOptions(string Root, int Port, string DataDirectory)
{
  public static HostOptions Parse(string[] args)
  {
    var root = AppContext.BaseDirectory;
    var port = 18080;
    var dataDirectory = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "PackStudio", "WebView2");
    for (var index = 0; index < args.Length; index += 2)
    {
      if (index + 1 >= args.Length)
        throw new ArgumentException($"缺少 {args[index]} 的值。");
      var value = args[index + 1];
      switch (args[index])
      {
        case "--root": root = Path.GetFullPath(value); break;
        case "--port":
          if (!int.TryParse(value, out port) || port < 0 || port > 65535)
            throw new ArgumentException("端口必须在 0 到 65535 之间。");
          break;
        case "--data-dir": dataDirectory = Path.GetFullPath(value); break;
        default: throw new ArgumentException($"未知参数：{args[index]}");
      }
    }
    return new HostOptions(root, port, dataDirectory);
  }
}
