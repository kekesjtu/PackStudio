using System.Data;
using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;
public partial class MainWindow
{
    internal static FrameworkElement Numeric(JToken? value, bool integer, string unit, Action<JToken> changed, double minimum = 0, double? maximum = null)
    {
        var border = new Border
        {
            BorderThickness = new(1),
            BorderBrush = Brushes.LightSlateGray,
            CornerRadius = new(2),
            Background = Brushes.White
        };
        var dock = new DockPanel();
        border.Child = dock;
        var text = new TextBox
        {
            Text = value?.Type == JTokenType.Null ? "" : value?.ToString() ?? "",
            BorderThickness = new(0),
            // 上下内边距比默认少 1px，抵掉外框 1px 边框，使输入框总高度与其他字段控件一致。
            Padding = new(6, 3, 6, 3),
            MinWidth = 60
        };
        if (integer)
        {
            var arrows = new Grid
            {
                Width = 22
            };
            arrows.RowDefinitions.Add(new() { Height = new GridLength(1, GridUnitType.Star) });
            arrows.RowDefinitions.Add(new() { Height = new GridLength(1, GridUnitType.Star) });
            // 箭头列跟随输入框高度，避免按钮自身高度把整个输入框撑高。
            arrows.SetBinding(FrameworkElement.HeightProperty, new System.Windows.Data.Binding(nameof(FrameworkElement.ActualHeight)) { Source = text });
            DockPanel.SetDock(arrows, Dock.Right);
            dock.Children.Add(arrows);
            foreach (int direction in new[]
            {
                1,
                -1
            }

            )
            {
                var button = new Button
                {
                    Content = new System.Windows.Shapes.Path
                    {
                        Data = Geometry.Parse(direction == 1 ? "M0,3 L5,3 L2.5,0 Z" : "M0,0 L5,0 L2.5,3 Z"),
                        Fill = Brushes.SlateGray,
                        HorizontalAlignment = HorizontalAlignment.Center,
                        VerticalAlignment = VerticalAlignment.Center
                    },
                    Padding = new(0),
                    Margin = new(0),
                    MinHeight = 0,
                    Focusable = false
                };
                button.Click += (_, _) =>
                {
                    if (double.TryParse(text.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out double n))
                        text.Text = Math.Clamp(Math.Truncate(n) + direction, minimum, maximum ?? long.MaxValue).ToString(CultureInfo.InvariantCulture);
                };
                Grid.SetRow(button, arrows.Children.Count);
                arrows.Children.Add(button);
            }
        }
        else if (unit.Length > 0)
        {
            var label = new TextBlock
            {
                Text = unit,
                Margin = new(5, 0, 7, 0),
                Foreground = Brushes.SlateGray,
                VerticalAlignment = VerticalAlignment.Center
            };
            DockPanel.SetDock(label, Dock.Right);
            dock.Children.Add(label);
        }

        dock.Children.Add(text);
        text.GotKeyboardFocus += (_, _) => text.SelectAll();
        text.TextChanged += (_, _) =>
        {
            if (string.IsNullOrWhiteSpace(text.Text))
            {
                text.Foreground = Brushes.Black;
                changed(JValue.CreateNull());
            }
            else if (double.TryParse(text.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out double n) && double.IsFinite(n) && n >= minimum && (!maximum.HasValue || n <= maximum.Value) && (!integer || n == Math.Truncate(n) && n >= long.MinValue && n < 9223372036854775808d))
            {
                text.Foreground = Brushes.Black;
                changed(integer ? new JValue(checked((long)n)) : new JValue(n));
            }
            else
            {
                text.Foreground = Brushes.Firebrick;
                changed(new JValue(text.Text));
            }
        };
        return border;
    }

    FrameworkElement Table(JArray rows, (string Key, string Label, Type Type)[] columns, Action<JArray> changed)
    {
        var table = new DataTable();
        foreach (var col in columns)
            table.Columns.Add(col.Key, col.Type);
        foreach (var record in rows)
        {
            var row = table.NewRow();
            foreach (var col in columns)
                row[col.Key] = record[col.Key]?.Type is null or JTokenType.Null ? col.Type == typeof(bool) ? false : DBNull.Value : record[col.Key]!.ToObject(col.Type)!;
            table.Rows.Add(row);
        }

        var grid = new DataGrid
        {
            ItemsSource = table.DefaultView,
            AutoGenerateColumns = false,
            CanUserAddRows = false,
            CanUserDeleteRows = true,
            MinHeight = 115,
            MaxHeight = 280,
            FontSize = 11,
            RowHeaderWidth = 16
        };
        foreach (var col in columns)
        {
            var binding = new System.Windows.Data.Binding(col.Key)
            {
                UpdateSourceTrigger = col.Type == typeof(bool) ? System.Windows.Data.UpdateSourceTrigger.PropertyChanged : System.Windows.Data.UpdateSourceTrigger.LostFocus
            };
            DataGridColumn column;
            if (col.Type == typeof(bool))
            {
                var checkbox = new FrameworkElementFactory(typeof(CheckBox));
                checkbox.SetValue(CheckBox.HorizontalAlignmentProperty, HorizontalAlignment.Center);
                checkbox.SetValue(CheckBox.VerticalAlignmentProperty, VerticalAlignment.Center);
                checkbox.SetBinding(CheckBox.IsCheckedProperty, binding);
                var template = new DataTemplate { VisualTree = checkbox };
                column = new DataGridTemplateColumn { CellTemplate = template };
            }
            else column = new DataGridTextColumn { Binding = binding };
            column.Header = col.Label;
            column.Width = new DataGridLength(1, DataGridLengthUnitType.Star);
            grid.Columns.Add(column);
        }

        void Update()
        {
            var array = new JArray();
            foreach (DataRow row in table.Rows)
            {
                if (row.RowState == DataRowState.Deleted)
                    continue;
                var o = new JObject();
                foreach (var col in columns)
                    o[col.Key] = row[col.Key] is DBNull ? JValue.CreateNull() : JToken.FromObject(row[col.Key]);
                array.Add(o);
            }

            changed(array);
        }

        grid.CellEditEnding += (_, _) => Dispatcher.BeginInvoke(Update);
        table.RowDeleted += (_, _) => Update();
        table.ColumnChanged += (_, e) =>
        {
            if (e.Column?.DataType == typeof(bool)) Dispatcher.BeginInvoke(Update);
        };
        var panel = new StackPanel();
        panel.Children.Add(grid);
        var buttons = new StackPanel { Orientation = Orientation.Horizontal, Margin = new(0, 6, 0, 0) };
        var add = new Button { Content = "+ 添加一行", Padding = new(10, 3, 10, 3), Margin = new(0) };
        var remove = new Button { Content = "删除选中行", Padding = new(10, 3, 10, 3), Margin = new(8, 0, 0, 0), IsEnabled = false };
        add.Click += (_, _) =>
        {
            grid.CommitEdit(DataGridEditingUnit.Row, true);
            var row = table.NewRow();
            foreach (var col in columns)
                row[col.Key] = col.Type == typeof(bool) ? false : col.Type == typeof(string) ? "" : 0;
            table.Rows.Add(row);
            Update();
            grid.SelectedItem = table.DefaultView[table.Rows.Count - 1];
            grid.ScrollIntoView(grid.SelectedItem);
        };
        remove.Click += (_, _) =>
        {
            grid.CommitEdit(DataGridEditingUnit.Row, true);
            foreach (var selected in grid.SelectedItems.Cast<DataRowView>().ToList())
                table.Rows.Remove(selected.Row);
            Update();
        };
        grid.SelectionChanged += (_, _) => remove.IsEnabled = grid.SelectedItems.Count > 0;
        buttons.Children.Add(add);
        buttons.Children.Add(remove);
        panel.Children.Add(buttons);
        return panel;
    }
}
