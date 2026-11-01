using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop.Tests;
static class RemovalMatrixChecks
{
    // 去球矩阵：框选矩形归一化、增删合并与写回顺序；界面按行列数生成格子并可单击切换。
    public static void Run(MainWindow window, ListBox steps, StackPanel fields, Workspace workspace)
    {
        var region = RemovalMatrix.Rectangle((2, 3), (0, 1)).ToList();
        if (region.Count != 9 || region[0] != (0, 1) || region[^1] != (2, 3))
            throw new Exception("框选矩形未按起点与终点归一化");
        if (RemovalMatrix.Merge([(1, 1)], [(1, 1), (1, 2)], false).Count != 0)
            throw new Exception("框选恢复未清除选中格子");
        if (RemovalMatrix.Merge([(1, 1)], [(1, 2), (2, 2)], true).Count != 3)
            throw new Exception("框选去除未并入选中格子");
        var ordered = RemovalMatrix.ToJson([(2, 1), (0, 3), (0, 1)]);
        if (ordered.ToString(Newtonsoft.Json.Formatting.None) != """[{"row":0,"column":1},{"row":0,"column":3},{"row":2,"column":1}]""")
            throw new Exception("去球单元写回顺序不稳定：" + ordered.ToString(Newtonsoft.Json.Formatting.None));

        if (steps.Items.Cast<WizardStep>().All(step => step.Key != "solder_removal"))
            return;
        var bga = workspace.Document.Bga;
        steps.SelectedValue = "solder_removal";
        window.UpdateLayout();
        int rows = (int)workspace.Document.Values["bga.rows"].Number(), columns = (int)workspace.Document.Values["bga.columns"].Number();
        var matrix = Descendants<ScrollViewer>(fields).Select(view => view.Content is Border frame ? frame.Child : view.Content).OfType<Grid>()
            .FirstOrDefault(grid => grid.RowDefinitions.Count == rows + 1 && grid.ColumnDefinitions.Count == columns + 1)
            ?? throw new Exception("去球单元缺少行列数对应的矩阵");
        var cells = matrix.Children.OfType<Border>().Where(cell => cell.Tag != null).ToList();
        if (cells.Count != rows * columns)
            throw new Exception($"去球矩阵格子数 {cells.Count} 与 {rows}×{columns} 不一致");
        var cell = cells[0];
        cell.RaiseEvent(Mouse(MouseButtonEvent.LeftDown, UIElement.MouseLeftButtonDownEvent));
        cell.RaiseEvent(Mouse(MouseButtonEvent.LeftUp, UIElement.MouseLeftButtonUpEvent));
        if ((bga["omitted_cells"] as JArray ?? []).Count != 1)
            throw new Exception("单击矩阵格子未写入去球单元");
        cell.RaiseEvent(Mouse(MouseButtonEvent.LeftDown, UIElement.MouseLeftButtonDownEvent));
        cell.RaiseEvent(Mouse(MouseButtonEvent.LeftUp, UIElement.MouseLeftButtonUpEvent));
        if ((bga["omitted_cells"] as JArray ?? []).Count != 0)
            throw new Exception("再次单击矩阵格子未恢复焊球");
    }

    static IEnumerable<T> Descendants<T>(DependencyObject root)
        where T : DependencyObject
    {
        for (int i = 0; i < System.Windows.Media.VisualTreeHelper.GetChildrenCount(root); i++)
        {
            var child = System.Windows.Media.VisualTreeHelper.GetChild(root, i);
            if (child is T match)
                yield return match;
            foreach (var nested in Descendants<T>(child))
                yield return nested;
        }
    }

    enum MouseButtonEvent { LeftDown, LeftUp }

    static MouseButtonEventArgs Mouse(MouseButtonEvent kind, RoutedEvent routed) =>
        new(System.Windows.Input.Mouse.PrimaryDevice, 0, MouseButton.Left) { RoutedEvent = routed };
}
