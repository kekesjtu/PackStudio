using System.Windows;
using System.Windows.Controls;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop.Tests;
static class TableEditorChecks
{
    static int covered;

    // 表格编辑器：没有选中行时删除按钮禁用，添加与删除都要写回数据。
    public static async Task Run(MainWindow window, ListBox steps, StackPanel fields, Workspace workspace)
    {
        foreach (var step in steps.Items.Cast<WizardStep>())
        {
            steps.SelectedValue = step.Key;
            window.UpdateLayout();
            var grid = Descendants<DataGrid>(fields).FirstOrDefault();
            if (grid == null)
                continue;
            var remove = Descendants<Button>(fields).FirstOrDefault(button => button.Content?.ToString() == "删除选中行")
                ?? throw new Exception(step.Key + ": 表格缺少删除按钮");
            var add = Descendants<Button>(fields).First(button => button.Content?.ToString() == "+ 添加一行");
            int before = grid.Items.Count, stored = StoredRows(workspace);
            if (remove.IsEnabled)
                throw new Exception(step.Key + ": 未选中行时删除按钮应禁用");
            add.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
            window.UpdateLayout();
            if (grid.Items.Count != before + 1 || StoredRows(workspace) != stored + 1)
                throw new Exception(step.Key + ": 添加一行未写回数据");
            if (!remove.IsEnabled)
                throw new Exception(step.Key + ": 选中新行后删除按钮应可用");
            remove.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
            window.UpdateLayout();
            if (grid.Items.Count != before || StoredRows(workspace) != stored)
                throw new Exception(step.Key + ": 删除选中行未写回数据");
            // 表格编辑结束会排队一次写回，等它落盘再继续，避免生成期间参数变动。
            await Task.Delay(50);
            covered++;
            return;
        }
    }

    public static void Verify()
    {
        if (covered == 0)
            throw new Exception("没有任何模板覆盖表格的添加与删除");
    }

    // 表格既可能写入向导字段（金属层、层表），也可能写入 BGA 配置（焊球坐标表）。
    static int StoredRows(Workspace workspace) =>
        workspace.Document.Values.Properties().Sum(p => Count(p.Value));

    static int Count(JToken token) => token switch
    {
        JArray array => array.Count,
        _ => 0
    };

    // 表格可能位于栏目滚动区之外尚未实例化，按逻辑树查找。
    static IEnumerable<T> Descendants<T>(DependencyObject root)
        where T : DependencyObject
    {
        foreach (var child in LogicalTreeHelper.GetChildren(root).OfType<DependencyObject>())
        {
            if (child is T match)
                yield return match;
            foreach (var nested in Descendants<T>(child))
                yield return nested;
        }
    }
}
