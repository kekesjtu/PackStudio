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
        var coordinates = ordered.Select(cell => (cell["row"]!.Value<int>(), cell["column"]!.Value<int>()));
        if (!coordinates.SequenceEqual(new[] { (0, 1), (0, 3), (2, 1) }))
            throw new Exception("去球单元写回顺序不稳定");

        if (steps.Items.Cast<WizardStep>().All(step => step.Key != "solder_removal"))
            return;
        var bga = workspace.Document.Values;
        steps.SelectedValue = "solder_removal";
        window.UpdateLayout();
        int rows = (int)workspace.Document.Values["bga.rows"].Number(), columns = (int)workspace.Document.Values["bga.columns"].Number();
        var balls = Box(fields, "显式去球") ?? throw new Exception("缺少显式去球勾选框");
        balls.IsChecked = true;
        Pump(window);
        var matrix = Matrix(fields, rows, columns) ?? throw new Exception("去球单元缺少行列数对应的矩阵");
        var cells = matrix.Children.OfType<Border>().Where(cell => cell.Tag != null).ToList();
        if (cells.Count != rows * columns)
            throw new Exception($"去球矩阵格子数 {cells.Count} 与 {rows}×{columns} 不一致");
        Click(cells[0]);
        if ((bga["bga.omitted_cells"] as JArray ?? []).Count != 1)
            throw new Exception("单击矩阵格子未写入去球单元");
        Click(cells[cells.Count - 1]);
        if ((bga["bga.omitted_cells"] as JArray ?? []).Count != 2)
            throw new Exception("分散点选未保留已去除格子");
        Click(cells[0]);
        if ((bga["bga.omitted_cells"] as JArray ?? []).Count != 1)
            throw new Exception("再次单击矩阵格子未恢复焊球");
        var reset = Descendants<Button>(fields).SingleOrDefault(button => button.Content?.ToString() == "重置为空")
            ?? throw new Exception("去球矩阵缺少重置按钮");
        reset.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
        if ((bga["bga.omitted_cells"] as JArray ?? []).Count != 0)
            throw new Exception("重置按钮未清空去球单元");

        if (steps.Items.Cast<WizardStep>().All(step => step.Key != "thermal_vias"))
            return;
        steps.SelectedValue = "thermal_vias";
        window.UpdateLayout();
        if (NumericBox(fields, "通孔 Y 方向数量") == null)
            return;
        var removal = RemovalBox(fields) ?? throw new Exception("热通孔缺少启用通孔去除选项");
        if (removal.IsChecked == true || Reset(fields) != null)
            throw new Exception("通孔去除默认未勾选且不展开参数");
        removal.IsChecked = true;
        Pump(window);
        int viaColumns = (int)workspace.Document.Values["vias.columns"].Number();
        int viaRows = (int)workspace.Document.Values["vias.rows"].Number();
        if (Matrix(fields, viaRows, viaColumns) != null || Reset(fields) != null)
            throw new Exception("去孔矩阵默认收起");
        var holes = Box(fields, "显式去孔") ?? throw new Exception("缺少显式去孔勾选框");
        holes.IsChecked = true;
        Pump(window);
        if (Matrix(fields, viaRows, viaColumns) == null || Reset(fields) == null)
            throw new Exception("勾选去孔后未展开去通孔单元");
        var rowCount = NumericBox(fields, "通孔 Y 方向数量") ?? throw new Exception("去通孔单元缺少通孔行数字段");
        string original = rowCount.Text;
        rowCount.Text = "3";
        window.UpdateLayout();
        var viaMatrix = Matrix(fields, 3, viaColumns);
        if (viaMatrix == null || viaMatrix.Children.OfType<Border>().Count(cell => cell.Tag != null) != 3 * viaColumns)
            throw new Exception("去孔矩阵未随阵列行列数重建");
        Click(viaMatrix.Children.OfType<Border>().First(cell => cell.Tag != null));
        if ((workspace.Document.Values["bga.via_configuration"]?["omitted_cells"] as JArray ?? []).Count != 1)
            throw new Exception("去孔单元未写回文档");
        Reset(fields)!.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
        rowCount.Text = original;
        window.UpdateLayout();
        RemovalBox(fields)!.IsChecked = false;
        Pump(window);
        if (Reset(fields) != null)
            throw new Exception("取消启用通孔去除后仍展示去通孔单元");

        var enabled = Descendants<CheckBox>(fields).Single(box => box.Content?.ToString()?.Contains("热通孔") == true);
        enabled.IsChecked = false;
        Pump(window);
        if (fields.Children.Count != 1 || Descendants<CheckBox>(fields).Count() != 1 || RemovalBox(fields) != null)
            throw new Exception("未启用热通孔时仍有参数控件");
        Descendants<CheckBox>(fields).Single().IsChecked = true;
        Pump(window);
    }

    static CheckBox? RemovalBox(StackPanel fields) => Box(fields, "启用通孔去除");

    static CheckBox? Box(StackPanel fields, string label) => fields.Children.OfType<CheckBox>().SingleOrDefault(box => box.Content?.ToString() == label);

    static Button? Reset(StackPanel fields) => Descendants<Button>(fields).FirstOrDefault(button => button.Content?.ToString() == "重置为空");

    static void Pump(Window window)
    {
        window.Dispatcher.Invoke(() => { }, System.Windows.Threading.DispatcherPriority.Background);
        window.UpdateLayout();
    }

    static Grid? Matrix(StackPanel fields, int rows, int columns) => Descendants<ScrollViewer>(fields)
        .Select(view => view.Content is Border frame ? frame.Child : view.Content).OfType<Grid>()
        .FirstOrDefault(grid => grid.RowDefinitions.Count == rows + 1 && grid.ColumnDefinitions.Count == columns + 1);

    static TextBox? NumericBox(StackPanel fields, string label) => fields.Children.OfType<Grid>()
        .Where(row => row.Children.OfType<DockPanel>().SelectMany(panel => panel.Children.OfType<TextBlock>()).Any(text => text.Text == label) ||
            row.Children.OfType<TextBlock>().Any(text => text.Text == label))
        .SelectMany(row => Descendants<TextBox>(row)).FirstOrDefault();

    static void Click(Border cell)
    {
        cell.RaiseEvent(Mouse(MouseButtonEvent.LeftDown, UIElement.MouseLeftButtonDownEvent));
        cell.RaiseEvent(Mouse(MouseButtonEvent.LeftUp, UIElement.MouseLeftButtonUpEvent));
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
