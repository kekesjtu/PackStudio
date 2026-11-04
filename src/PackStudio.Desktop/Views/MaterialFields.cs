using System.Windows;
using System.Windows.Controls;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;
public sealed partial class ParameterPanel
{
    void AddMaterial(JToken selection)
    {
        string group = selection["group_id"].Text();
        var choices = MaterialSelection.Choices(workspace.Catalog, workspace.Template, workspace.Document, selection);
        string id = choices.SelectedId;
        var allowed = choices.Items;
        var groups = new ComboBox
        {
            ItemsSource = allowed.Select(m => m.Category).Distinct().Order().ToList(),
        };
        var box = new ComboBox
        {
            ItemTemplate = MaterialPresentation.Template(),
            HorizontalContentAlignment = HorizontalAlignment.Stretch,
            VerticalContentAlignment = VerticalAlignment.Center,
            ItemContainerStyle = new Style(typeof(ComboBoxItem)) { Setters = { new Setter(Control.HorizontalContentAlignmentProperty, HorizontalAlignment.Stretch) } },
            SelectedValuePath = "Id"
        };
        void Filter(bool select)
        {
            var candidates = allowed.Where(m => m.Category == groups.SelectedItem?.ToString()).OrderBy(m => m.Name).ToList();
            box.ItemsSource = candidates.Select(m => new MaterialPresentation.Option(m)).ToList();
            box.SelectedValue = select ? candidates.FirstOrDefault()?.Id : id;
        }

        groups.SelectedItem = allowed.FirstOrDefault(m => m.Id == id)?.Category ?? allowed.FirstOrDefault()?.Category;
        Filter(false);
        groups.SelectionChanged += (_, _) => Filter(true);
        box.SelectionChanged += (_, _) =>
        {
            if (box.SelectedValue is string value)
            {
                workspace.Document.MaterialAssignments[group] = value;
                workspace.Dirty();
            }
        };
        FieldsPanel.Children.Add(new Separator { Margin = new(0, 4, 0, 8) });
        FieldsPanel.Children.Add(FieldRow("材料组", groups));
        FieldsPanel.Children.Add(FieldRow(selection["label"].Text(), box));
    }
}
