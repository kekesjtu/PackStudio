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
    // checkboxInEditor: 勾选框放在编辑列，标签留在标签列，用于创建选项这类表单式布局。
    public static FrameworkElement Create(ParameterField field, bool checkboxInEditor = false)
    {
        var f = field.Definition;
        string control = field.Type;
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
                var box = new CheckBox { Content = checkboxInEditor ? null : field.Label, ToolTip = field.Label,
                    VerticalAlignment = VerticalAlignment.Center };
                Bind(box, CheckBox.IsCheckedProperty, field, nameof(ParameterField.BooleanValue));
                if (checkboxInEditor) editors.Children.Add(box);
                else
                {
                    host.Children.RemoveAt(0); Grid.SetColumn(editors, 0); Grid.SetColumnSpan(editors, 3);
                    editors.Children.Add(box);
                }
            }
            else if (field.Options is { Count: > 0 } options)
            {
                var box = new ComboBox { ItemsSource = options.Select(o => new { Value = o["value"]!.DeepClone(), Label = o["label"].Text(o["value"]!.ToString()) }).ToList(), DisplayMemberPath = "Label", SelectedValuePath = "Value" };
                Bind(box, ComboBox.SelectedValueProperty, field, nameof(ParameterField.ChoiceValue));
                editors.Children.Add(box);
            }
            else if (control == "table")
            {
                host.RowDefinitions.Add(new() { Height = GridLength.Auto }); host.RowDefinitions.Add(new() { Height = GridLength.Auto });
                Grid.SetColumnSpan(host.Children[0], 3); Grid.SetColumn(editors, 0); Grid.SetColumnSpan(editors, 3); Grid.SetRow(editors, 1);
                editors.Margin = new(0, 6, 0, 0);
                var columns = ((JArray)f["columns"]!).Select(c => (c["key"].Text(), c["label"].Text(), c["type"].Text() switch { "checkbox" => typeof(bool), "text" => typeof(string), _ => typeof(double) }, ParameterField.Bounds(c))).ToArray();
                editors.Children.Add(Table(field, field.Value is JArray table ? (JArray)table.DeepClone() : [], columns));
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
