using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using PackStudio.Core;

namespace PackStudio.Desktop;
public partial class MainWindow
{
    static Grid FieldRow(string label, FrameworkElement editor)
    {
        var row = new Grid
        {
            Margin = new(0, 0, 0, 7)
        };
        row.ColumnDefinitions.Add(new() { Width = new GridLength(135) });
        row.ColumnDefinitions.Add(new());
        row.Children.Add(new TextBlock { Text = label, TextWrapping = TextWrapping.Wrap, VerticalAlignment = VerticalAlignment.Center, HorizontalAlignment = HorizontalAlignment.Right, Margin = new(0, 0, 10, 0) });
        Grid.SetColumn(editor, 1);
        row.Children.Add(editor);
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
            ReadOnly("Outline Type", "Standard Outline");
            ReadOnly("Die Type", "Actual Die");
        }

        if (document.Values["substrate.layers"] != null)
            ReadOnly("基板层数", document.Values["substrate.layers"].Text());
        FieldsPanel.Children.Add(FieldRow("芯片功率", Numeric(document.Values["die.power"], false, "W", value =>
        {
            document.Values["die.power"] = value;
            workspace.Dirty();
        })));
    }
}
