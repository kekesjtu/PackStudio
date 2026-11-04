using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static PackStudio.Desktop.FieldLayout;

namespace PackStudio.Desktop;
public sealed partial class ParameterPanel
{
    void AddSummary()
    {
        var definitions = (JArray)workspace.Template.Ui.Steps.Single(s => s["key"].Text() == "summary")["fields"]!;
        foreach (var definition in definitions)
        {
            var field = new SummaryField(workspace, form, definition);
            FrameworkElement editor;
            if (field.Editable)
            {
                var text = new TextBox { MaxLength = field.MaximumLength };
                text.SetBinding(TextBox.TextProperty, new Binding(nameof(SummaryField.Text)) { Source = field, Mode = BindingMode.TwoWay, UpdateSourceTrigger = UpdateSourceTrigger.PropertyChanged });
                editor = text;
            }
            else
            {
                var text = new TextBlock { TextWrapping = TextWrapping.Wrap, Margin = new(5, 5, 0, 5) };
                text.SetBinding(TextBlock.TextProperty, new Binding(nameof(SummaryField.Text)) { Source = field });
                editor = text;
            }
            var row = FieldRow(field.Label, editor, new Binding(nameof(SummaryField.Symbol)) { Source = field });
            row.DataContext = field;
            row.SetBinding(UIElement.VisibilityProperty, new Binding(nameof(SummaryField.Visible)) { Source = field, Converter = new BooleanToVisibilityConverter() });
            FieldsPanel.Children.Add(row);
        }
    }
}
