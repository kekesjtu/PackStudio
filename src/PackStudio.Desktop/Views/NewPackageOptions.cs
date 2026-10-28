using System.Windows;
using System.Windows.Controls;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;
public partial class NewPackageWindow
{
    IEnumerable<JToken> CreationFields() => template.Fields.Where(f => PackagePresentation.IsCreationOption(f["key"].Text()) && JsonData.Matches(f["visible_when"] as JObject, Draft.Values));
    void RefreshCreationOptions()
    {
        CreationOptions.Children.Clear();
        foreach (var field in CreationFields())
        {
            string key = field["key"].Text(), control = field["control"].Text();
            var row = new Grid
            {
                Margin = new(0, 0, 0, 10)
            };
            row.ColumnDefinitions.Add(new() { Width = new GridLength(130) });
            row.ColumnDefinitions.Add(new());
            row.Children.Add(new TextBlock { Text = field["label"].Text(), TextWrapping = TextWrapping.Wrap, VerticalAlignment = VerticalAlignment.Center, HorizontalAlignment = HorizontalAlignment.Right, Margin = new(0, 0, 12, 0) });
            FrameworkElement editor;
            if (control == "checkbox")
            {
                var checkbox = new CheckBox
                {
                    IsChecked = Draft.Values[key].Flag(),
                    VerticalAlignment = VerticalAlignment.Center,
                    Content = "启用"
                };
                checkbox.Checked += (_, _) => Draft.Values[key] = true;
                checkbox.Unchecked += (_, _) => Draft.Values[key] = false;
                editor = checkbox;
            }
            else if (field["options"] is JArray { Count: > 0 } options)
            {
                var choices = options.Select(o => new { Value = o.DeepClone(), Label = field["option_labels"]?[o.ToString()].Text(o.ToString()) ?? o.ToString() }).ToList();
                var box = new ComboBox
                {
                    ItemsSource = choices,
                    SelectedValuePath = "Value",
                    DisplayMemberPath = "Label",
                    SelectedValue = Draft.Values[key]
                };
                box.SelectionChanged += (_, _) =>
                {
                    if (box.SelectedValue is JToken value)
                        Draft.Values[key] = value.DeepClone();
                };
                editor = box;
            }
            else
                editor = MainWindow.Numeric(Draft.Values[key], control.StartsWith("integer"), field["unit"].Text(), value => Draft.Values[key] = value);
            editor.IsEnabled = JsonData.Matches(field["enabled_when"] as JObject, Draft.Values);
            editor.Tag = key;
            Grid.SetColumn(editor, 1);
            row.Children.Add(editor);
            CreationOptions.Children.Add(row);
        }
    }
}
