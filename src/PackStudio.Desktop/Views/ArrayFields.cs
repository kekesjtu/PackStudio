using System.Data;
using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
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
        string id = workspace.Document.Assignments.GetValueOrDefault(group, preset?.Materials[group].Text(selection["default"].Text()) ?? selection["default"].Text());
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
        bool initialized = false;
        void Filter(bool select)
        {
            var candidates = allowed.Where(m => m.Category == groups.SelectedItem?.ToString()).OrderBy(m => m.Name).ToList();
            box.ItemsSource = candidates.Select(m => new MaterialPresentation.Option(m)).ToList();
            box.SelectedValue = select ? candidates.FirstOrDefault()?.Id : id;
        }

        groups.SelectedItem = allowed.FirstOrDefault(m => m.Id == id)?.Category ?? allowed.FirstOrDefault()?.Category;
        Filter(false);
        initialized = true;
        groups.SelectionChanged += (_, _) => Filter(true);
        box.SelectionChanged += (_, _) =>
        {
            if (initialized && box.SelectedValue is string value)
            {
                workspace.Document.Assignments[group] = value;
                workspace.Dirty();
            }
        };
        FieldsPanel.Children.Add(new Separator { Margin = new(0, 4, 0, 8) });
        FieldsPanel.Children.Add(FieldRow("材料组", groups));
        FieldsPanel.Children.Add(FieldRow(selection["label"].Text(), box));
    }

    void AddBga(string step)
    {
        var b = workspace.Document.Bga;
        if (step == "central_solder_balls")
        {
            ConfigCheck(b, "center_solder_enabled", "包含中央焊球");
            ConfigCheck(b, "center_staggered", "中央焊球交错");
            ConfigNumber(b, "center_solder_rows", "中央焊球行数");
            ConfigNumber(b, "center_solder_columns", "中央焊球列数");
            return;
        }
        if (step == "solder_removal")
        {
            ConfigCheck(b, "solder_removal_enabled", "主阵列中心去球");
            ConfigNumber(b, "populated_rows", "外围满布行数");
            ConfigNumber(b, "populated_columns", "外围满布列数");
            AddRemovalCells("balls", "显式去球", b, "bga.rows", "bga.columns");
            return;
        }

        FieldsPanel.Children.Add(new TextBlock { Text = "焊球阵列", FontWeight = FontWeights.SemiBold, Margin = new(0, 10, 0, 10) });
        ConfigCheck(b, "staggered", "交错主阵列");
        ConfigCheck(b, "ball_map_enabled", "使用焊球坐标表");
        FieldsPanel.Children.Add(new TextBlock { Text = "焊球坐标表（mm）", Margin = new(0, 10, 0, 5) });
        FieldsPanel.Children.Add(Table(b["ball_map"] as JArray ?? [], [("id", "ID", typeof(string)), ("x", "X", typeof(double)), ("y", "Y", typeof(double))], a =>
        {
            b["ball_map"] = a;
            workspace.Dirty();
        }));
    }

    void AddBgaModeling()
    {
        if (workspace.Template.Fields.All(f => f["step"].Text() != "solder_balls"))
            return;
        var b = workspace.Document.Bga;
        string[] reps = workspace.Document.TemplateId == "chip_array" ? ["discrete"] : workspace.Document.TemplateId == "pbga_wb" ? ["discrete", "equivalent", "isotropic"] : ["discrete", "equivalent"];
        var box = new ComboBox
        {
            ItemsSource = reps.Select(r => new { Id = r, Label = r == "discrete" ? "Discrete Cuboids" : r == "equivalent" ? "Orthotropic Cuboid" : "Isotropic Cuboid" }),
            DisplayMemberPath = "Label",
            SelectedValuePath = "Id",
            SelectedValue = b["representation"].Text()
        };
        box.SelectionChanged += (_, _) =>
        {
            b["representation"] = box.SelectedValue?.ToString();
            workspace.Dirty();
        };
        FieldsPanel.Children.Add(FieldRow("焊球建模方式", box));
    }

    void AddViaConfiguration()
    {
        if (!workspace.Document.Values["vias.enabled"].Flag())
            return;
        if (workspace.Document.Bga["via_configuration"] is not JObject v)
        {
            v = new JObject();
            workspace.Document.Bga["via_configuration"] = v;
        }
        ConfigCheck(v, "removal_enabled", "启用通孔去除", () =>
        {
            v["removal_rows"] ??= 0;
            v["removal_columns"] ??= 0;
            Dispatcher.BeginInvoke(RefreshFields);
        });
        if (!v["removal_enabled"].Flag())
            return;
        ConfigNumber(v, "removal_rows", "中央去除行数");
        ConfigNumber(v, "removal_columns", "中央去除列数");
        AddRemovalCells("vias", "显式去孔", v, "vias.rows", "vias.columns");
    }

    void AddRemovalCells(string id, string label, JObject data, string rowsKey, string columnsKey)
    {
        bool expanded = Expanders.TryGetValue(id, out bool stored) ? stored : (data["omitted_cells"] as JArray)?.Count > 0;
        var box = new CheckBox { Content = label, IsChecked = expanded, Margin = new(0, 10, 0, 5) };
        box.Checked += (_, _) => Expand(id, true);
        box.Unchecked += (_, _) => Expand(id, false);
        FieldsPanel.Children.Add(box);
        if (!expanded)
            return;
        var host = new ContentControl();
        void Rebuild() => host.Content = RemovalMatrix.Build(data["omitted_cells"] as JArray ?? [], Count(rowsKey), Count(columnsKey), a =>
        {
            data["omitted_cells"] = a;
            workspace.Dirty();
        });
        Rebuild();
        Refreshers.Add((rowsKey, Rebuild));
        Refreshers.Add((columnsKey, Rebuild));
        FieldsPanel.Children.Add(host);
    }

    void Expand(string id, bool expanded)
    {
        Expanders[id] = expanded;
        Dispatcher.BeginInvoke(RefreshFields);
    }

    void ConfigCheck(JObject data, string key, string label, Action? changed = null)
    {
        var box = new CheckBox
        {
            Content = label,
            IsChecked = data[key].Flag(),
            Margin = new(0, 9, 0, 5)
        };
        void Set(bool value)
        {
            data[key] = value;
            changed?.Invoke();
            workspace.Dirty();
        }
        box.Checked += (_, _) => Set(true);
        box.Unchecked += (_, _) => Set(false);
        FieldsPanel.Children.Add(box);
    }

    void ConfigNumber(JObject data, string key, string label)
    {
        string symbol = key switch
        {
            "populated_rows" => "MEp", "populated_columns" => "MDp",
            "center_solder_rows" => "MEc", "center_solder_columns" => "MDc",
            _ => ""
        };
        FieldsPanel.Children.Add(FieldRow(label, Numeric(data[key], true, "", v =>
        {
            data[key] = v;
            workspace.Dirty();
        }), symbol: symbol));
    }

    int Count(string key) => (int)workspace.Document.Values[key].Number();
}
