using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;

namespace PackStudio.Desktop;

public static class FieldLayout
{
    public static Grid FieldRow(string label, FrameworkElement editor, ParameterField? field = null)
    {
        var row = new Grid { Margin = new(0, 0, 0, 7), DataContext = field };
        row.ColumnDefinitions.Add(new() { Width = GridLength.Auto, MinWidth = 64, SharedSizeGroup = "ParameterLabels" });
        row.ColumnDefinitions.Add(new());
        row.ColumnDefinitions.Add(new() { Width = new GridLength(72) });
        var text = new TextBlock { Text = label, ToolTip = label, TextTrimming = TextTrimming.CharacterEllipsis,
            VerticalAlignment = VerticalAlignment.Center };
        if (field == null)
        {
            text.Margin = new(0, 0, 10, 0);
            row.Children.Add(text);
        }
        else
        {
            var panel = new DockPanel { Margin = new(0, 0, 10, 0) };
            var symbol = new TextBlock { VerticalAlignment = VerticalAlignment.Center };
            symbol.SetBinding(TextBlock.TextProperty, new Binding(nameof(ParameterField.Symbol)) { Source = field, StringFormat = " {0}" });
            DockPanel.SetDock(symbol, Dock.Right);
            panel.Children.Add(symbol);
            panel.Children.Add(text);
            row.Children.Add(panel);
        }
        Grid.SetColumn(editor, 1);
        row.Children.Add(editor);
        return row;
    }
}
