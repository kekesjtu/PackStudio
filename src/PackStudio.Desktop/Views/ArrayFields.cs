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
        FieldsPanel.Children.Add(new TextBlock { Text = selection["label"].Text(), Margin = new(0, 5, 0, 5) });
        var groups = new ComboBox
        {
            ItemsSource = allowed.Select(m => m.Category).Distinct().Order().ToList(),
            Margin = new(0, 0, 0, 4)
        };
        var box = new ComboBox
        {
            DisplayMemberPath = "Name",
            SelectedValuePath = "Id",
            Margin = new(0, 0, 0, 15)
        };
        bool initialized = false;
        void Filter(bool select)
        {
            var candidates = allowed.Where(m => m.Category == groups.SelectedItem?.ToString()).OrderBy(m => m.Name).ToList();
            box.ItemsSource = candidates;
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
        FieldsPanel.Children.Add(groups);
        FieldsPanel.Children.Add(box);
    }

    void AddBga()
    {
        var b = workspace.Document.Bga;
        FieldsPanel.Children.Add(new TextBlock { Text = "焊球建模与阵列", FontWeight = FontWeights.SemiBold, Margin = new(0, 10, 0, 10) });
        string[] reps = workspace.Document.TemplateId == "chip_array" ? ["discrete"] : workspace.Document.TemplateId == "pbga_wb" ? ["discrete", "equivalent", "isotropic"] : ["discrete", "equivalent"];
        var representation = new ComboBox
        {
            ItemsSource = reps.Select(r => new { Id = r, Label = r == "discrete" ? "离散矩形块" : r == "equivalent" ? "各向异性等效层" : "各向同性等效层" }),
            DisplayMemberPath = "Label",
            SelectedValuePath = "Id",
            SelectedValue = b["representation"].Text()
        };
        representation.SelectionChanged += (_, _) =>
        {
            b["representation"] = representation.SelectedValue?.ToString();
            workspace.Dirty();
        };
        FieldsPanel.Children.Add(representation);
        foreach (var(key, label)in new[]
        {
            ("staggered", "交错主阵列"),
            ("solder_removal_enabled", "主阵列中心去球"),
            ("center_solder_enabled", "包含中央焊球"),
            ("center_staggered", "中央焊球交错"),
            ("ball_map_enabled", "使用焊球坐标表")
        }

        )
            ConfigCheck(b, key, label);
        foreach (var(key, label)in new[]
        {
            ("populated_rows", "外围满布行数"),
            ("populated_columns", "外围满布列数"),
            ("center_solder_rows", "中央焊球行数"),
            ("center_solder_columns", "中央焊球列数")
        }

        )
            ConfigNumber(b, key, label);
        FieldsPanel.Children.Add(new TextBlock { Text = "显式去球单元（从 0 开始）", Margin = new(0, 10, 0, 5) });
        FieldsPanel.Children.Add(Table(b["omitted_cells"] as JArray ?? [], [("row", "行", typeof(int)), ("column", "列", typeof(int))], a =>
        {
            b["omitted_cells"] = a;
            workspace.Dirty();
        }));
        FieldsPanel.Children.Add(new TextBlock { Text = "焊球坐标表（mm）", Margin = new(0, 10, 0, 5) });
        FieldsPanel.Children.Add(Table(b["ball_map"] as JArray ?? [], [("id", "ID", typeof(string)), ("x", "X", typeof(double)), ("y", "Y", typeof(double))], a =>
        {
            b["ball_map"] = a;
            workspace.Dirty();
        }));
    }

    void AddViaConfiguration()
    {
        var v = workspace.Document.Bga["via_configuration"] as JObject ?? new();
        workspace.Document.Bga["via_configuration"] = v;
        ConfigCheck(v, "removal_enabled", "启用通孔去除");
        ConfigNumber(v, "removal_rows", "中央去除行数");
        ConfigNumber(v, "removal_columns", "中央去除列数");
        FieldsPanel.Children.Add(Table(v["omitted_cells"] as JArray ?? [], [("row", "去除行", typeof(int)), ("column", "去除列", typeof(int))], a =>
        {
            v["omitted_cells"] = a;
            workspace.Dirty();
        }));
    }

    void ConfigCheck(JObject data, string key, string label)
    {
        var box = new CheckBox
        {
            Content = label,
            IsChecked = data[key].Flag(),
            Margin = new(0, 9, 0, 5)
        };
        box.Checked += (_, _) =>
        {
            data[key] = true;
            workspace.Dirty();
        };
        box.Unchecked += (_, _) =>
        {
            data[key] = false;
            workspace.Dirty();
        };
        FieldsPanel.Children.Add(box);
    }

    void ConfigNumber(JObject data, string key, string label)
    {
        FieldsPanel.Children.Add(new TextBlock { Text = label, Margin = new(0, 8, 0, 4) });
        FieldsPanel.Children.Add(Numeric(data[key], true, "", v =>
        {
            data[key] = v;
            workspace.Dirty();
        }));
    }
}
