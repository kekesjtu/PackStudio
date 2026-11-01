using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;

// 去球、去通孔单元的矩阵选择：单击切换单个格子，按住左键拖动即框选一块矩形区域。
public static class RemovalMatrix
{
    const double CellSize = 15;
    static readonly SolidColorBrush Line = new(Color.FromRgb(0x9A, 0xA3, 0xAE));
    static readonly SolidColorBrush Kept = new(Colors.White);
    static readonly SolidColorBrush Taken = new(Color.FromRgb(0x6F, 0x7F, 0x8E));
    static readonly SolidColorBrush AddPreview = new(Color.FromRgb(0x9E, 0xC2, 0xE8));
    static readonly SolidColorBrush RemovePreview = new(Color.FromRgb(0xD5, 0xD9, 0xDD));

    sealed record Cell(int Row, int Column);

    public static FrameworkElement Build(JArray cells, int rows, int columns, Action<JArray> apply)
    {
        if (rows <= 0 || columns <= 0)
            return new TextBlock { Text = "先填写阵列行列数。", Foreground = Brushes.SlateGray, TextWrapping = TextWrapping.Wrap };
        var taken = new HashSet<(int Row, int Column)>();
        int outside = 0;
        foreach (var cell in cells.OfType<JObject>())
        {
            int row = (int)cell["row"].Number(), column = (int)cell["column"].Number();
            if (row >= 0 && row < rows && column >= 0 && column < columns)
                taken.Add((row, column));
            else
                outside++;
        }

        var grid = new Grid { HorizontalAlignment = HorizontalAlignment.Left, Background = Brushes.Transparent };
        grid.ColumnDefinitions.Add(new() { Width = GridLength.Auto });
        grid.RowDefinitions.Add(new() { Height = GridLength.Auto });
        for (int column = 0; column < columns; column++)
            grid.ColumnDefinitions.Add(new() { Width = new GridLength(CellSize) });
        for (int row = 0; row < rows; row++)
            grid.RowDefinitions.Add(new() { Height = new GridLength(CellSize) });

        var body = new Border[rows, columns];
        var preview = new HashSet<(int Row, int Column)>();
        var anchor = (Row: 0, Column: 0);
        bool adding = true, dragging = false;
        var caption = new TextBlock { Foreground = Brushes.DimGray, TextWrapping = TextWrapping.Wrap, Margin = new(0, 0, 0, 5) };

        void Report() => caption.Text = $"已去除 {taken.Count} 格（共 {rows} × {columns} 格），拖动可框选整块。" +
            (outside > 0 ? $"另有 {outside} 个单元超出当前阵列，需删除。" : "");
        void Repaint()
        {
            for (int row = 0; row < rows; row++)
                for (int column = 0; column < columns; column++)
                {
                    var key = (row, column);
                    body[row, column].Background = preview.Contains(key) ? adding ? AddPreview : RemovePreview : taken.Contains(key) ? Taken : Kept;
                }
        }

        void Extend((int Row, int Column) corner)
        {
            preview.Clear();
            foreach (var key in Rectangle(anchor, corner))
                preview.Add(key);
            Repaint();
        }

        void Commit()
        {
            dragging = false;
            if (preview.Count == 0)
                return;
            taken.Clear();
            taken.UnionWith(Merge(taken, preview, adding));
            preview.Clear();
            Repaint();
            Report();
            apply(ToJson(taken));
        }

        grid.Children.Add(Header(""));
        for (int column = 0; column < columns; column++)
        {
            var header = Header((column + 1).ToString());
            Grid.SetColumn(header, column + 1);
            grid.Children.Add(header);
        }

        for (int row = 0; row < rows; row++)
        {
            var header = Header((row + 1).ToString());
            Grid.SetRow(header, row + 1);
            grid.Children.Add(header);
            for (int column = 0; column < columns; column++)
            {
                var cell = new Border
                {
                    BorderBrush = Line,
                    BorderThickness = new(0, 0, 1, 1),
                    Background = Kept,
                    Tag = new Cell(row, column),
                    ToolTip = $"第 {row + 1} 行 第 {column + 1} 列"
                };
                int r = row, c = column;
                cell.MouseLeftButtonDown += (_, _) =>
                {
                    anchor = (r, c);
                    adding = !taken.Contains((r, c));
                    dragging = true;
                    cell.CaptureMouse();
                    Extend(anchor);
                };
                cell.MouseMove += (_, _) =>
                {
                    if (!dragging || Mouse.LeftButton != MouseButtonState.Pressed)
                        return;
                    if (CellAt(grid, Mouse.GetPosition(grid)) is Cell hover)
                        Extend((hover.Row, hover.Column));
                };
                cell.MouseLeftButtonUp += (_, _) =>
                {
                    if (!dragging)
                        return;
                    Commit();
                    cell.ReleaseMouseCapture();
                };
                cell.LostMouseCapture += (_, _) =>
                {
                    if (dragging)
                        Commit();
                };
                Grid.SetRow(cell, row + 1);
                Grid.SetColumn(cell, column + 1);
                body[row, column] = cell;
                grid.Children.Add(cell);
            }
        }

        // 鼠标在格子外松开时兜底提交，避免框选状态残留。
        grid.MouseLeftButtonUp += (_, _) =>
        {
            if (dragging)
                Commit();
        };
        Report();
        Repaint();
        return new StackPanel
        {
            Margin = new(0, 2, 0, 0),
            Children =
            {
                caption,
                new ScrollViewer
                {
                    Content = new Border { BorderBrush = Line, BorderThickness = new(1), HorizontalAlignment = HorizontalAlignment.Left, Child = grid },
                    HorizontalScrollBarVisibility = ScrollBarVisibility.Auto,
                    VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                    MaxHeight = 240
                }
            }
        };
    }

    public static IEnumerable<(int Row, int Column)> Rectangle((int Row, int Column) anchor, (int Row, int Column) corner)
    {
        for (int row = Math.Min(anchor.Row, corner.Row); row <= Math.Max(anchor.Row, corner.Row); row++)
            for (int column = Math.Min(anchor.Column, corner.Column); column <= Math.Max(anchor.Column, corner.Column); column++)
                yield return (row, column);
    }

    public static HashSet<(int Row, int Column)> Merge(IEnumerable<(int Row, int Column)> taken, IEnumerable<(int Row, int Column)> region, bool adding)
    {
        var result = new HashSet<(int Row, int Column)>(taken);
        if (adding)
            result.UnionWith(region);
        else
            result.ExceptWith(region);
        return result;
    }

    public static JArray ToJson(IEnumerable<(int Row, int Column)> taken) =>
        new(taken.OrderBy(c => c.Row).ThenBy(c => c.Column).Select(c => (JToken)new JObject { ["row"] = c.Row, ["column"] = c.Column }));

    static TextBlock Header(string text) => new()
    {
        Text = text,
        FontSize = 8,
        Foreground = Brushes.DimGray,
        HorizontalAlignment = HorizontalAlignment.Center,
        VerticalAlignment = VerticalAlignment.Center,
        Margin = new(1, 0, 1, 0),
        IsHitTestVisible = false
    };

    static Cell? CellAt(UIElement root, Point point)
    {
        var hit = root.InputHitTest(point) as DependencyObject;
        while (hit != null && hit is not Border)
            hit = VisualTreeHelper.GetParent(hit);
        return (hit as Border)?.Tag as Cell;
    }
}
