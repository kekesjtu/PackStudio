using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;

namespace PackStudio.Desktop;

public static class FieldLayout
{
    public static Grid FieldRow(string label, FrameworkElement editor, BindingBase? symbolBinding = null)
    {
        var row = Row();
        row.ColumnDefinitions.Add(new() { Width = GridLength.Auto, MinWidth = 64, SharedSizeGroup = "ParameterLabels" });
        row.ColumnDefinitions.Add(new());
        row.ColumnDefinitions.Add(new() { Width = new GridLength(72) });
        var text = Label(label);
        if (symbolBinding == null)
        {
            text.SetResourceReference(FrameworkElement.MarginProperty, "FieldLabelSpacing");
            row.Children.Add(text);
        }
        else
        {
            var panel = new DockPanel();
            panel.SetResourceReference(FrameworkElement.MarginProperty, "FieldLabelSpacing");
            var symbol = new TextBlock { VerticalAlignment = VerticalAlignment.Center, Margin = new(4, 0, 0, 0) };
            symbol.SetBinding(TextBlock.TextProperty, symbolBinding);
            DockPanel.SetDock(symbol, Dock.Right);
            panel.Children.Add(symbol);
            panel.Children.Add(text);
            row.Children.Add(panel);
        }
        Grid.SetColumn(editor, 1);
        editor.VerticalAlignment = VerticalAlignment.Center;
        row.Children.Add(editor);
        return row;
    }

    public static TextBlock Label(string label) => new()
    {
        Text = label, ToolTip = label, TextTrimming = TextTrimming.CharacterEllipsis,
        VerticalAlignment = VerticalAlignment.Center
    };

    public static Grid FullWidthRow(FrameworkElement content)
    {
        var row = Row();
        content.VerticalAlignment = VerticalAlignment.Center;
        row.Children.Add(content);
        return row;
    }

    static Grid Row()
    {
        var row = new Grid();
        row.SetResourceReference(FrameworkElement.StyleProperty, "FieldRow");
        return row;
    }

    public static Grid HeaderBodyRow(FrameworkElement header, FrameworkElement body)
    {
        var row = FullWidthRow(header);
        var line = new RowDefinition { Height = GridLength.Auto };
        line.MinHeight = (double)row.FindResource("FieldLineHeight");
        row.RowDefinitions.Add(line);
        row.RowDefinitions.Add(new() { Height = GridLength.Auto });
        body.SetResourceReference(FrameworkElement.MarginProperty, "FieldBodySpacing");
        Grid.SetRow(body, 1);
        row.Children.Add(body);
        return row;
    }
}
