using System.Windows;
using System.Windows.Controls;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;
public partial class MainWindow
{
    void AddMaterial(JToken selection)
    {
        string group = selection["group_id"].Text();
        var options = (JArray)selection["options"]!;
        var allowed = workspace.Catalog.Materials.Items.Values.Where(m => options.Any(o => o.Text() == "*" || o.Text() == m.Id)).ToList();
        var preset = workspace.Template.Presets.FirstOrDefault(p => p.Id == workspace.Document.PresetId);
        string id = workspace.Document.MaterialAssignments.GetValueOrDefault(group, preset?.MaterialAssignments[group].Text(selection["default"].Text()) ?? selection["default"].Text());
        if (id.Length > 0 && allowed.All(m => m.Id != id) && workspace.Catalog.Materials.Items.TryGetValue(id, out var current))
            allowed.Add(current);
        allowed = allowed.GroupBy(m => m.Name).Select(g => g.FirstOrDefault(m => m.Id == id) ?? g.OrderBy(m => m.Id.Length).ThenBy(m => m.Id).First()).ToList();
        allowed = allowed.Select(m => workspace.Document.CustomMaterials.FirstOrDefault(c => c.Id == m.Id) ?? m).ToList();
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
