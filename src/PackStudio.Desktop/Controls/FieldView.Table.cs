using System.Data;
using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;
public static partial class FieldView
{
    static FrameworkElement Table(JArray rows, (string Key, string Label, Type Type)[] columns, Action<JArray> changed)
    {
        var table = new DataTable();
        foreach (var col in columns)
            table.Columns.Add(col.Key, typeof(object));
        foreach (var record in rows)
        {
            var row = table.NewRow();
            foreach (var col in columns)
            {
                var value = (record as JObject)?[col.Key];
                row[col.Key] = value is JValue scalar ? scalar.Value ?? DBNull.Value : value?.DeepClone() ?? (object)DBNull.Value;
            }
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
            column.SortMemberPath = col.Key;
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
                {
                    object value = row[col.Key];
                    o[col.Key] = value is DBNull ? JValue.CreateNull() : col.Type == typeof(double) && value is string text
                        ? FieldValues.Parse(new JObject { ["control"] = "number" }, text) : JToken.FromObject(value);
                }
                array.Add(o);
            }

            changed(array);
        }

        grid.CellEditEnding += (_, _) => grid.Dispatcher.BeginInvoke(Update);
        table.RowDeleted += (_, _) => Update();
        table.ColumnChanged += (_, e) =>
        {
            if (columns.Any(c => c.Key == e.Column?.ColumnName && c.Type == typeof(bool))) grid.Dispatcher.BeginInvoke(Update);
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
