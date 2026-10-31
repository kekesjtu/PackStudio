using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using PackStudio.Core;

namespace PackStudio.Desktop;
public partial class MainWindow
{
    static Grid FieldRow(string label, FrameworkElement editor, FrameworkElement? suffix = null, string symbol = "")
    {
        var row = new Grid
        {
            Margin = new(0, 0, 0, 7)
        };
        row.ColumnDefinitions.Add(new() { Width = new GridLength(105) });
        row.ColumnDefinitions.Add(new());
        row.ColumnDefinitions.Add(new() { Width = new GridLength(72) });
        string display = symbol.Length > 0 && label.EndsWith(" " + symbol, StringComparison.Ordinal) ? label[..^(symbol.Length + 1)] : label;
        var text = new TextBlock { Text = display, ToolTip = symbol.Length > 0 ? label + " (" + symbol + ")" : label, TextTrimming = TextTrimming.CharacterEllipsis, TextWrapping = TextWrapping.NoWrap, VerticalAlignment = VerticalAlignment.Center, HorizontalAlignment = HorizontalAlignment.Right };
        if (symbol.Length == 0)
        {
            text.Margin = new(0, 0, 10, 0);
            row.Children.Add(text);
        }
        else
        {
            var labelPanel = new DockPanel { Margin = new(0, 0, 10, 0), LastChildFill = true };
            var symbolText = new TextBlock { Text = " " + symbol, VerticalAlignment = VerticalAlignment.Center, ToolTip = symbol };
            DockPanel.SetDock(symbolText, Dock.Right);
            labelPanel.Children.Add(symbolText);
            labelPanel.Children.Add(text);
            row.Children.Add(labelPanel);
        }
        Grid.SetColumn(editor, 1);
        row.Children.Add(editor);
        if (suffix != null)
        {
            Grid.SetColumn(suffix, 2);
            row.Children.Add(suffix);
        }
        return row;
    }

    void AddSummary()
    {
        var document = workspace.Document;
        var name = new TextBox
        {
            Text = document.Name,
            MaxLength = 160
        };
        name.TextChanged += Name_Changed;
        FieldsPanel.Children.Add(FieldRow("设计名称", name));
        void ReadOnly(string label, string value) => FieldsPanel.Children.Add(FieldRow(label, new TextBlock { Text = value, TextWrapping = TextWrapping.Wrap, Margin = new(5, 5, 0, 5) }));
        ReadOnly("封装类型", workspace.Template.Info.Name);
        if (document.PresetId.Length > 0)
        {
            ReadOnly("JEDEC Footprint", document.PresetId);
        }

        if (document.Values["substrate.layers"] != null)
            ReadOnly("基板层数", document.Values["substrate.layers"].Text());
        ReadOnly("芯片功率", document.Values["die.power"].Text() + " W");

    }
}
