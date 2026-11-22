using System.Diagnostics;
using System.IO;
using PackStudio.Core;

namespace PackStudio.Desktop;

internal static class PtaHandoff
{
    const string ExecutableName = "PTA.exe";
    static string DataDirectory => Path.Combine(App.LocalDataRoot, "PTA");
    static string ExecutableSetting => Path.Combine(DataDirectory, "executable-path.txt");

    public static string? FindExecutable()
    {
        string defaultPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "PTA", ExecutableName);
        if (File.Exists(defaultPath))
            return defaultPath;

        if (!File.Exists(ExecutableSetting))
            return null;

        string path = File.ReadAllText(ExecutableSetting).Trim();
        return IsPtaExecutable(path) ? path : null;
    }

    public static void RememberExecutable(string path)
    {
        if (!IsPtaExecutable(path))
            throw new ArgumentException("请选择本机安装的 PTA.exe。", nameof(path));

        Directory.CreateDirectory(DataDirectory);
        File.WriteAllText(ExecutableSetting, path);
    }

    public static string Export(GenerationResult result)
    {
        string directory = Path.Combine(DataDirectory, "Projects");
        Directory.CreateDirectory(directory);
        string fileName = FormattableString.Invariant($"{DateTime.Now:yyyyMMdd-HHmmss}-{Guid.NewGuid():N}.pta.xml");
        string path = Path.Combine(directory, fileName);
        PtaProjectExporter.Save(result, path);
        return path;
    }

    public static void Open(string executable, string projectPath)
    {
        var startInfo = new ProcessStartInfo(executable)
        {
            WorkingDirectory = Path.GetDirectoryName(executable),
            UseShellExecute = false
        };
        startInfo.ArgumentList.Add(projectPath);
        using var process = Process.Start(startInfo) ?? throw new InvalidOperationException("Windows 未能启动 PTA。");
    }

    static bool IsPtaExecutable(string path) => Path.IsPathFullyQualified(path)
        && string.Equals(Path.GetFileName(path), ExecutableName, StringComparison.OrdinalIgnoreCase)
        && File.Exists(path);
}
