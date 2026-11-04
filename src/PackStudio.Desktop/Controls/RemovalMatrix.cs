using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;

// 去球、去孔的矩阵选择：单击切换单个格子，按住左键拖动即框选一块矩形区域。
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
        void ReadCells(JArray source)
        {
            taken.Clear(); outside = 0;
            foreach (var cell in source)
            {
                if (cell is not JObject coordinate || !Index(coordinate["row"], out int row) || !Index(coordinate["column"], out int column))
                {
                    outside++;
                    continue;
                }
                if (row >= 0 && row < rows && column >= 0 && column < columns) taken.Add((row, column));
                else outside++;
            }
        }
        static bool Index(JToken? value, out int index)
        {
            index = 0;
            if (value?.Type is not (JTokenType.Integer or JTokenType.Float)) return false;
            double number = value.Value<double>();
            if (!double.IsFinite(number) || number != Math.Truncate(number) || number < int.MinValue || number > int.MaxValue) return false;
            index = (int)number;
            return true;
        }
        ReadCells(cells);

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
        var caption = new TextBlock { Foreground = Brushes.DimGray, VerticalAlignment = VerticalAlignment.Center, TextWrapping = TextWrapping.Wrap };
        var reset = new Button { Content = "重置为空", Padding = new Thickness(8, 3, 8, 3), Margin = new Thickness(8, 0, 0, 6), HorizontalAlignment = HorizontalAlignment.Right };

        // 分散点选、框选与重置都走同一套写回路径。
        void Report()
        {
            caption.Text = $"已去除 {taken.Count} / {rows * columns} 格" +
                (outside > 0 ? $"（{outside} 个单元无效或超出当前阵列，需删除）" : "");
            reset.IsEnabled = taken.Count > 0 || outside > 0;
        }
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
            var merged = Merge(taken, preview, adding);
            taken.Clear();
            taken.UnionWith(merged);
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
        reset.Click += (_, _) =>
        {
            if (taken.Count == 0 && outside == 0)
                return;
            taken.Clear();
            outside = 0;
            preview.Clear();
            Repaint();
            Report();
            apply(ToJson(taken));
        };

        var head = new DockPanel { LastChildFill = true, Margin = new(0, 0, 0, 5) };
        DockPanel.SetDock(reset, Dock.Right);
        head.Children.Add(reset);
        head.Children.Add(caption);

        Report();
        Repaint();
        return new RemovalMatrixView(source => { ReadCells(source); Repaint(); Report(); })
        {
            Margin = new(0, 2, 0, 0),
            Children =
            {
                head,
                new ScrollViewer
                {
                    Content = new Border { BorderBrush = Line, BorderThickness = new(1), HorizontalAlignment = HorizontalAlignment.Left, Child = grid },
                    HorizontalScrollBarVisibility = ScrollBarVisibility.Auto,
                    VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                    MaxHeight = 240,
                    ToolTip = "单击切换单个格子，按住左键拖动可框选整块。"
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
