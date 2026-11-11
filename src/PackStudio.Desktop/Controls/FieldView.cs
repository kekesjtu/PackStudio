using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Media;
using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static PackStudio.Desktop.FieldLayout;

namespace PackStudio.Desktop;

public enum CheckBoxPlacement { FullRow, EditorColumn }

public static partial class FieldView
{
    static readonly BooleanToVisibilityConverter VisibilityConverter = new();
    public static FrameworkElement Create(ParameterField field, CheckBoxPlacement checkBoxPlacement = CheckBoxPlacement.FullRow)
    {
        var f = field.Definition;
        string control = field.Type;
        FrameworkElement view;
        if (control == "removal_matrix")
        {
            var box = BooleanEditor(field, nameof(ParameterField.Expanded), field.Label);
            var matrix = new RemovalMatrixEditor(field);
            VisibilityBinding(matrix, field, nameof(ParameterField.Expanded));
            view = HeaderBodyRow(box, matrix);
        }
        else if (control == "checkbox")
        {
            bool inEditor = checkBoxPlacement == CheckBoxPlacement.EditorColumn;
            var editors = new StackPanel();
            editors.Children.Add(BooleanEditor(field, nameof(ParameterField.BooleanValue), inEditor ? null : field.Label));
            AddHelp(editors, field);
            view = inEditor ? FieldRow(field.Label, editors) : FullWidthRow(editors);
        }
        else if (control == "table")
        {
            var editors = new StackPanel();
            var columns = ((JArray)f["columns"]!).Select(c => (c["key"].Text(), c["label"].Text(), c["type"].Text() switch { "checkbox" => typeof(bool), "text" => typeof(string), _ => typeof(double) }, ParameterField.Bounds(c))).ToArray();
            editors.Children.Add(Table(field, field.Value is JArray table ? (JArray)table.DeepClone() : [], columns));
            AddHelp(editors, field);
            view = HeaderBodyRow(Label(field.Label), editors);
        }
        else
        {
            var editors = new StackPanel();
            var host = FieldRow(field.Label, editors, new Binding(nameof(ParameterField.Symbol)) { Source = field });
            view = host;
            if (field.Options is { Count: > 0 } options)
            {
                var box = new ComboBox { ItemsSource = options.Select(o => new { Value = o["value"]!.DeepClone(), Label = o["label"].Text(o["value"]!.ToString()) }).ToList(), DisplayMemberPath = "Label", SelectedValuePath = "Value" };
                Bind(box, ComboBox.SelectedValueProperty, field, nameof(ParameterField.ChoiceValue));
                editors.Children.Add(box);
            }
            else if (control is "number" or "integer")
            {
                editors.Children.Add(new NumericEditor(field));
                var hint = new TextBlock { FontSize = 10, Foreground = Brushes.SlateGray, VerticalAlignment = VerticalAlignment.Center, Margin = new(6, 0, 0, 0), TextTrimming = TextTrimming.CharacterEllipsis };
                Bind(hint, TextBlock.TextProperty, field, nameof(ParameterField.Range), BindingMode.OneWay);
                Grid.SetColumn(hint, 2); host.Children.Add(hint);
            }
            else
            {
                var text = new TextBox();
                Bind(text, TextBox.TextProperty, field, nameof(ParameterField.TextValue), BindingMode.TwoWay);
                editors.Children.Add(text);
            }
            AddHelp(editors, field);
        }
        view.DataContext = field;
        Bind(view, UIElement.IsEnabledProperty, field, nameof(ParameterField.Enabled), BindingMode.OneWay);
        VisibilityBinding(view, field);
        return view;
    }

    static CheckBox BooleanEditor(ParameterField field, string property, string? label)
    {
        var box = new CheckBox { Content = label, ToolTip = field.Label };
        box.SetResourceReference(FrameworkElement.StyleProperty, "FormCheckBox");
        Bind(box, CheckBox.IsCheckedProperty, field, property);
        return box;
    }

    static void AddHelp(StackPanel editors, ParameterField field)
    {
        if (field.Definition["help_text"].Text() is string help && help.Length > 0)
            editors.Children.Add(new TextBlock { Text = help, TextWrapping = TextWrapping.Wrap, Foreground = Brushes.SlateGray, FontSize = 11 });
    }

    public static void VisibilityBinding(FrameworkElement view, ParameterField field, string property = nameof(ParameterField.Visible)) =>
        view.SetBinding(UIElement.VisibilityProperty, new Binding(property) { Source = field, Converter = VisibilityConverter });
    static void Bind(FrameworkElement view, DependencyProperty property, ParameterField field, string name, BindingMode mode = BindingMode.TwoWay) =>
        view.SetBinding(property, new Binding(name) { Source = field, Mode = mode, UpdateSourceTrigger = UpdateSourceTrigger.PropertyChanged });
}
