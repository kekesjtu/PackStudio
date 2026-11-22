using System.Windows.Threading;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;

namespace PackStudio.Desktop;

public partial class MainWindow
{
    bool CanSendToPta() => !workspace.IsBusy;

    [RelayCommand(CanExecute = nameof(CanSendToPta))]
    async Task SendToPtaAsync()
    {
        string? exportedPath = null;
        try
        {
            if (!parameters.CommitTableEdits())
            {
                workspace.Status = "请完成参数表格中的编辑后再交接 PTA 工程。";
                return;
            }
            // Apply the table's queued value update before capturing the workspace revision.
            await Dispatcher.InvokeAsync(() => { }, DispatcherPriority.Background);
            if (workspace.IsBusy)
                return;

            long revision = workspace.Revision;
            if (!workspace.IsCurrent)
                await workspace.GenerateAsync();
            if (workspace.Revision != revision || !workspace.CanExport || workspace.Result is not { } result)
                return;

            string? executable = null;
            if (!ptaSessionId.HasValue)
            {
                executable = FindOrSelectPta();
                if (executable == null || workspace.Revision != revision)
                    return;
            }

            workspace.Status = "正在导出 PTA 工程…";
            exportedPath = await Task.Run(() => PtaHandoff.Export(result));
            if (workspace.Revision != revision)
            {
                if (!workspace.IsBusy)
                    workspace.Status = "导出期间方案有修改，请重新交接 PTA 工程。";
                return;
            }

            if (ptaSessionId is { } session)
            {
                workspace.Status = "等待 PTA 确认打开工程…";
                await PtaSession.SendAsync(session, exportedPath);
                workspace.Status = "已传回 PTA 并打开工程：" + exportedPath;
            }
            else
            {
                PtaHandoff.Open(executable!, exportedPath);
                workspace.Status = "已导出工程并请求 PTA 打开：" + exportedPath;
            }
        }
        catch (Exception ex)
        {
            ShowError(exportedPath == null
                ? $"无法准备 PTA 工程。\n{ex.Message}"
                : $"PTA 工程交接未完成。\n{ex.Message}\n\n已导出的工程：\n{exportedPath}");
        }
    }

    string? FindOrSelectPta()
    {
        if (PtaHandoff.FindExecutable() is { } executable)
            return executable;

        var dialog = new OpenFileDialog
        {
            Title = "选择本机安装的 PTA.exe",
            Filter = "PTA 程序|PTA.exe",
            CheckFileExists = true
        };
        if (dialog.ShowDialog(this) != true)
            return null;

        PtaHandoff.RememberExecutable(dialog.FileName);
        return dialog.FileName;
    }
}
