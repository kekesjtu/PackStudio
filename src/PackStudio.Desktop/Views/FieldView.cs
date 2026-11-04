using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Media;
using Newtonsoft.Json.Linq;
using PackStudio.Core;
using static PackStudio.Desktop.FieldLayout;

namespace PackStudio.Desktop;

public static partial class FieldView
{
    static readonly BooleanToVisibilityConverter VisibilityConverter = new();
    public static FrameworkElement Create(ParameterField field)
    {
        var f = field.Definition;
        string control = field.Control;
        FrameworkElement view;
        if (control == "removal_matrix")
        {
            var panel = new StackPanel();
            var box = new CheckBox { Content = field.Label, Margin = new(0, 10, 0, 5) };
            Bind(box, CheckBox.IsCheckedProperty, field, nameof(ParameterField.Expanded));
            panel.Children.Add(box);
            var matrix = new RemovalMatrixEditor(field);
            VisibilityBinding(matrix, field, nameof(ParameterField.Expanded));
            panel.Children.Add(matrix);
            view = panel;
        }
        else
        {
            var editors = new StackPanel();
            var host = FieldRow(field.Label, editors, new Binding(nameof(ParameterField.Symbol)) { Source = field });
            view = host;
            if (control == "checkbox")
            {
                var box = new CheckBox { Content = field.Label, ToolTip = field.Label };
                Bind(box, CheckBox.IsCheckedProperty, field, nameof(ParameterField.BooleanValue));
                if (f["standalone"].Flag()) view = box;
                else
                {
                    host.Children.RemoveAt(0); Grid.SetColumn(editors, 0); Grid.SetColumnSpan(editors, 3);
                    editors.Children.Add(box);
                }
            }
            else if (field.Options is { Count: > 0 } options)
            {
                var box = new ComboBox { ItemsSource = options.Select(o => new { Value = o.DeepClone(), Label = f["option_labels"]?[o.ToString()].Text(o.ToString()) ?? o.ToString() }).ToList(), DisplayMemberPath = "Label", SelectedValuePath = "Value" };
                Bind(box, ComboBox.SelectedValueProperty, field, nameof(ParameterField.ChoiceValue));
                editors.Children.Add(box);
            }
            else if (control == "table")
            {
                host.RowDefinitions.Add(new() { Height = GridLength.Auto }); host.RowDefinitions.Add(new() { Height = GridLength.Auto });
                Grid.SetColumnSpan(host.Children[0], 3); Grid.SetColumn(editors, 0); Grid.SetColumnSpan(editors, 3); Grid.SetRow(editors, 1);
                editors.Margin = new(0, 6, 0, 0);
                var columns = ((JArray)f["columns"]!).Select(c => (c["key"].Text(), c["label"].Text(), c["type"].Text() switch { "checkbox" => typeof(bool), "text" => typeof(string), _ => typeof(double) })).ToArray();
                editors.Children.Add(Table(field.Value is JArray table ? (JArray)table.DeepClone() : [], columns, field.Set));
            }
            else if (control is "number" or "integer" or "integer_spinbox")
            {
                editors.Children.Add(new NumericEditor(field));
                double minimum = f["minimum"]?.Number() ?? 0;
                string range = f["maximum"]?.Type is JTokenType.Integer or JTokenType.Float ? $"{minimum} – {f["maximum"]!.Number()}" : $"≥ {minimum}";
                var hint = new TextBlock { Text = range, ToolTip = range, FontSize = 10, Foreground = Brushes.SlateGray, VerticalAlignment = VerticalAlignment.Center, Margin = new(6, 0, 0, 0), TextTrimming = TextTrimming.CharacterEllipsis };
                Grid.SetColumn(hint, 2); host.Children.Add(hint);
            }
            else
            {
                var text = new TextBox { IsReadOnly = control == "derived" };
                Bind(text, TextBox.TextProperty, field, control == "derived" ? nameof(ParameterField.DerivedValue) : nameof(ParameterField.TextValue), control == "derived" ? BindingMode.OneWay : BindingMode.TwoWay);
                editors.Children.Add(text);
            }
            if (f["help_text"].Text() is string help && help.Length > 0) editors.Children.Add(new TextBlock { Text = help, TextWrapping = TextWrapping.Wrap, Foreground = Brushes.SlateGray, FontSize = 11 });
        }
        view.DataContext = field;
        Bind(view, UIElement.IsEnabledProperty, field, nameof(ParameterField.Enabled), BindingMode.OneWay);
        VisibilityBinding(view, field);
        return view;
    }

    public static void VisibilityBinding(FrameworkElement view, ParameterField field, string property = nameof(ParameterField.Visible)) =>
        view.SetBinding(UIElement.VisibilityProperty, new Binding(property) { Source = field, Converter = VisibilityConverter });
    static void Bind(FrameworkElement view, DependencyProperty property, ParameterField field, string name, BindingMode mode = BindingMode.TwoWay) =>
        view.SetBinding(property, new Binding(name) { Source = field, Mode = mode, UpdateSourceTrigger = UpdateSourceTrigger.PropertyChanged });
}
