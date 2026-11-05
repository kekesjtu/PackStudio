using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using static PackStudio.Desktop.FieldLayout;

namespace PackStudio.Desktop;
public sealed partial class ParameterPanel
{
    void AddSummary()
    {
        var name = new TextBox { MaxLength = 160 };
        name.SetBinding(TextBox.TextProperty, new Binding(nameof(Workspace.DesignName))
        {
            Source = workspace, Mode = BindingMode.TwoWay, UpdateSourceTrigger = UpdateSourceTrigger.PropertyChanged
        });
        FieldsPanel.Children.Add(FieldRow("设计名称", name));
        FieldsPanel.Children.Add(FieldRow("封装类型", new TextBlock
        {
            Text = workspace.Template.Info.Name, TextWrapping = TextWrapping.Wrap, Margin = new(5, 5, 0, 5)
        }));
    }
}
