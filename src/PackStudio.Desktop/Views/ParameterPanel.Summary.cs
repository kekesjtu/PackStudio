using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using PackStudio.Core;
using static PackStudio.Desktop.FieldLayout;

namespace PackStudio.Desktop;
public sealed partial class ParameterPanel
{
    void AddSummary()
    {
        var document = workspace.Document;
        var name = new TextBox
        {
            Text = document.Name,
            MaxLength = 160
        };
        name.TextChanged += (_, _) => { workspace.Rename(name.Text); };
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
