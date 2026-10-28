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
    static FrameworkElement Numeric(JToken? value, bool integer, string unit, Action<JToken> changed)
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
            MinWidth = 60
        };
        if (integer)
        {
            var arrows = new StackPanel
            {
                Width = 22
            };
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
                    Content = direction == 1 ? "▴" : "▾",
                    Padding = new(0),
                    Margin = new(0),
                    Height = 16,
                    Focusable = false
                };
                button.Click += (_, _) =>
                {
                    if (double.TryParse(text.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out double n))
                        text.Text = (Math.Truncate(n) + direction).ToString(CultureInfo.InvariantCulture);
                };
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
            else if (double.TryParse(text.Text, NumberStyles.Float, CultureInfo.InvariantCulture, out double n) && double.IsFinite(n) && (!integer || n == Math.Truncate(n)))
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

    DataGrid Table(JArray rows, (string Key, string Label, Type Type)[] columns, Action<JArray> changed)
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
            CanUserAddRows = true,
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
                UpdateSourceTrigger = System.Windows.Data.UpdateSourceTrigger.LostFocus
            };
            DataGridColumn column = col.Type == typeof(bool) ? new DataGridCheckBoxColumn
            {
                Binding = binding
            }

            : new DataGridTextColumn
            {
                Binding = binding
            };
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
        return grid;
    }
}
