using System.IO;
using System.IO.Pipes;
using System.Text;
using System.Text.Json;
using PackStudio.Desktop;

namespace PackStudio.Desktop.Tests;

static class PtaSessionChecks
{
    public static async Task Run(MainWindow standalone)
    {
        if (standalone.FindName("PtaButton") is not Fluent.Button { Header: "在\u00A0PTA\u00A0中打开" })
            throw new Exception("standalone mode must offer to open the project in PTA");

        Guid sessionId = Guid.NewGuid();
        using var server = new NamedPipeServerStream($"PackStudio.PTA.{sessionId:N}", PipeDirection.InOut, 1,
            PipeTransmissionMode.Byte, PipeOptions.Asynchronous | PipeOptions.CurrentUserOnly);
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(30));
        var window = new MainWindow(sessionId) { ShowInTaskbar = false, ShowActivated = false, Opacity = 0 };
        var loaded = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        window.Loaded += (_, _) => loaded.TrySetResult();
        string? exportedPath = null;
        window.Show();
        try
        {
            var workspace = (Workspace)window.DataContext;
            await loaded.Task.WaitAsync(timeout.Token);
            while (workspace.IsBusy)
                await Task.Delay(20, timeout.Token);
            workspace.Select("bare_die");
            if (window.FindName("PtaButton") is not Fluent.Button { Header: "传回\u00A0PTA", IsEnabled: true } button
                || !ReferenceEquals(button.Command, window.SendToPtaCommand))
                throw new Exception("session mode must bind the return action to the ribbon button");

            var transfer = window.SendToPtaCommand.ExecuteAsync(null);
            var connection = server.WaitForConnectionAsync(timeout.Token);
            if (await Task.WhenAny(connection, transfer) == transfer)
                throw new Exception("return ended before connecting to PTA: " + workspace.Status);
            await connection;
            using var reader = new StreamReader(server, Encoding.UTF8, leaveOpen: true);
            string request = await reader.ReadLineAsync(timeout.Token) ?? throw new Exception("missing transfer request");
            using var json = JsonDocument.Parse(request);
            exportedPath = json.RootElement.GetProperty("projectPath").GetString();
            if (json.RootElement.GetProperty("version").GetInt32() != 1 || exportedPath == null
                || !Path.IsPathFullyQualified(exportedPath) || !exportedPath.EndsWith(".pta.xml") || !File.Exists(exportedPath))
                throw new Exception("PTA must receive the absolute path of the completed project file");
            if (!workspace.CanExport || transfer.IsCompleted || !workspace.Status.Contains("等待 PTA"))
                throw new Exception("return must generate the dirty model and await PTA's reply");

            await server.WriteAsync("{\"version\":1,\"opened\":true}\n"u8.ToArray(), timeout.Token);
            await transfer.WaitAsync(timeout.Token);
            if (!workspace.Status.StartsWith("已传回 PTA"))
                throw new Exception("successful PTA acknowledgment must reach the desktop status bar");
            Console.WriteLine("PASS PTA session button, model generation, export and acknowledgment");
        }
        finally
        {
            window.Close();
            if (exportedPath != null) File.Delete(exportedPath);
        }
    }
}
