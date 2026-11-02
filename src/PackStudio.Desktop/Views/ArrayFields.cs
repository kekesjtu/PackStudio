using System.Windows;
using System.Windows.Controls;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;
public partial class MainWindow
{
    void AddBga(string step)
    {
        var b = workspace.Document.Values;
        if (step == "central_solder_balls")
        {
            ConfigCheck(b, "bga.center_solder_enabled", "包含中央焊球");
            ConfigCheck(b, "bga.center_staggered", "中央焊球交错");
            ConfigNumber(b, "bga.center_solder_rows", "中央焊球行数");
            ConfigNumber(b, "bga.center_solder_columns", "中央焊球列数");
            return;
        }
        if (step == "solder_removal")
        {
            ConfigCheck(b, "bga.solder_removal_enabled", "主阵列中心去球");
            ConfigNumber(b, "bga.populated_rows", "外围满布行数");
            ConfigNumber(b, "bga.populated_columns", "外围满布列数");
            AddRemovalCells("balls", "显式去球", b, "bga.rows", "bga.columns", "bga.omitted_cells");
            return;
        }

        FieldsPanel.Children.Add(new TextBlock { Text = "焊球阵列", FontWeight = FontWeights.SemiBold, Margin = new(0, 10, 0, 10) });
        ConfigCheck(b, "bga.staggered", "交错主阵列");
        ConfigCheck(b, "bga.ball_map_enabled", "使用焊球坐标表");
        FieldsPanel.Children.Add(new TextBlock { Text = "焊球坐标表（mm）", Margin = new(0, 10, 0, 5) });
        FieldsPanel.Children.Add(Table(b["bga.ball_map"] as JArray ?? [], [("id", "ID", typeof(string)), ("x", "X", typeof(double)), ("y", "Y", typeof(double))], a =>
        {
            b["bga.ball_map"] = a;
            workspace.Dirty();
        }));
    }

    void AddBgaModeling()
    {
        if (workspace.Template.Fields.All(f => f["step"].Text() != "solder_balls"))
            return;
        var b = workspace.Document.Values;
        string[] reps = workspace.Document.TemplateId == "chip_array" ? ["discrete"] : workspace.Document.TemplateId == "pbga_wb" ? ["discrete", "equivalent", "isotropic"] : ["discrete", "equivalent"];
        var box = new ComboBox
        {
            ItemsSource = reps.Select(r => new { Id = r, Label = r == "discrete" ? "Discrete Cuboids" : r == "equivalent" ? "Orthotropic Cuboid" : "Isotropic Cuboid" }),
            DisplayMemberPath = "Label",
            SelectedValuePath = "Id",
            SelectedValue = b["bga.representation"].Text()
        };
        box.SelectionChanged += (_, _) =>
        {
            b["bga.representation"] = box.SelectedValue?.ToString();
            workspace.Dirty();
        };
        FieldsPanel.Children.Add(FieldRow("焊球建模方式", box));
    }

    void AddViaConfiguration()
    {
        if (!workspace.Document.Values["vias.enabled"].Flag())
            return;
        if (workspace.Document.Values["bga.via_configuration"] is not JObject v)
        {
            v = new JObject();
            workspace.Document.Values["bga.via_configuration"] = v;
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

    void AddRemovalCells(string id, string label, JObject data, string rowsKey, string columnsKey, string cellsKey = "omitted_cells")
    {
        bool expanded = Expanders.TryGetValue(id, out bool stored) ? stored : (data[cellsKey] as JArray)?.Count > 0;
        var box = new CheckBox { Content = label, IsChecked = expanded, Margin = new(0, 10, 0, 5) };
        box.Checked += (_, _) => Expand(id, true);
        box.Unchecked += (_, _) => Expand(id, false);
        FieldsPanel.Children.Add(box);
        if (!expanded)
            return;
        var host = new ContentControl();
        void Rebuild() => host.Content = RemovalMatrix.Build(data[cellsKey] as JArray ?? [], Count(rowsKey), Count(columnsKey), a =>
        {
            data[cellsKey] = a;
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
            "bga.populated_rows" => "MEp", "bga.populated_columns" => "MDp",
            "bga.center_solder_rows" => "MEc", "bga.center_solder_columns" => "MDc",
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
