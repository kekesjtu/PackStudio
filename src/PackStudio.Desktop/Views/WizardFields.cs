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
    static readonly Dictionary<string, string> Labels = new()
    {
        ["summary"] = "概要",
        ["package_setup"] = "封装规格",
        ["overall_package"] = "整体封装",
        ["package_substrate"] = "封装基板",
        ["upper_built_up"] = "上部增层区域",
        ["lower_built_up"] = "下部增层区域",
        ["die"] = "芯片",
        ["encapsulant"] = "塑封",
        ["flip_chip_bumps"] = "倒装芯片凸点",
        ["solder_balls"] = "BGA 焊球",
        ["central_solder_balls"] = "中央焊球",
        ["solder_removal"] = "焊球去除",
        ["die_flag_solder_mask"] = "承载台与阻焊层",
        ["die_flag_tie_bars"] = "承载台与连接筋",
        ["thermal_vias"] = "热通孔",
        ["backside_spreader"] = "背面扩散片",
        ["metal_layers"] = "金属层",
        ["lead_solder_interconnect"] = "引脚与焊料互连",
        ["dap"] = "芯片承载焊盘",
        ["thermal_land"] = "散热焊盘",
        ["thermal_land_solder"] = "散热焊盘与焊料",
        ["top_cover"] = "顶部结构",
        ["slug"] = "嵌入式散热块",
        ["modeling"] = "建模与局部网格",
        ["bumped_die"] = "凸点芯片",
        ["leadframe"] = "引线框",
        ["bond_wires"] = "键合线"
    };
    static string StepLabel(string key) => Labels.GetValueOrDefault(key, key);
    static bool IsLocalGridField(JToken field)
    {
        string key = field["key"].Text();
        return key.StartsWith("grid.", StringComparison.Ordinal) || key.Contains(".grid.", StringComparison.Ordinal);
    }

    readonly List<(string Key, Action Rebuild)> Refreshers = [];
    readonly Dictionary<string, bool> Expanders = [];
    void RefreshFields()
    {
        FieldsPanel.Children.Clear();
        Refreshers.Clear();
        if (StepList.SelectedValue is not string step)
            return;
        SectionTitle.Text = StepLabel(step);
        if (step == "summary")
        {
            AddSummary();
            AlignFieldRows();
            return;
        }

        var values = workspace.Document.Values;
        var fields = workspace.Template.Fields.Where(f => f["step"].Text() == step && f["control"].Text() is not ("footprint" or "configuration")).ToList();

        void AddField(JToken f)
        {
            if (!JsonData.Matches(f["visible_when"] as JObject, values))
                return;
            string key = f["key"].Text(), control = f["control"].Text();
            bool isTable = control is "table" or "metal_layers" or "layer_table";
            var editors = new StackPanel();
            string label = f["label"].Text();
            string symbol = control is "number" or "integer" or "integer_spinbox" ? DesFieldLabels.Symbol(f, values["substrate.layers"].Text()) : "";
            var host = FieldRow(label, editors, symbol: symbol);
            host.IsEnabled = JsonData.Matches(f["enabled_when"] as JObject, values);
            if (isTable)
            {
                host.RowDefinitions.Add(new() { Height = GridLength.Auto });
                host.RowDefinitions.Add(new() { Height = GridLength.Auto });
                Grid.SetColumnSpan(host.Children[0], 3);
                ((TextBlock)host.Children[0]).HorizontalAlignment = HorizontalAlignment.Left;
                Grid.SetColumn(editors, 0);
                Grid.SetColumnSpan(editors, 3);
                Grid.SetRow(editors, 1);
                editors.Margin = new(0, 6, 0, 0);
            }

            void Set(JToken? value, bool refresh = false)
            {
                values[key] = value ?? JValue.CreateNull();
                workspace.Dirty();
                if (refresh)
                    Dispatcher.BeginInvoke(RefreshFields);
                else
                    foreach (var rebuild in Refreshers.Where(r => r.Key == key).Select(r => r.Rebuild).ToList())
                        rebuild();
            }

            if (control == "checkbox")
            {
                host.Children.RemoveAt(0);
                Grid.SetColumn(editors, 0);
                Grid.SetColumnSpan(editors, 3);
                var box = new CheckBox
                {
                    IsChecked = values[key].Flag(),
                    Content = label,
                    ToolTip = label
                };
                box.Checked += (_, _) => Set(true, true);
                box.Unchecked += (_, _) => Set(false, true);
                editors.Children.Add(box);
            }
            else if (f["options"] is JArray options && options.Count > 0)
            {
                var choices = options.Select(o => new { Value = o.DeepClone(), Label = f["option_labels"]?[o.ToString()].Text(o.ToString()) ?? o.ToString() }).ToList();
                var box = new ComboBox
                {
                    ItemsSource = choices,
                    DisplayMemberPath = "Label",
                    SelectedValuePath = "Value",
                    SelectedValue = values[key]
                };
                box.SelectionChanged += (_, _) =>
                {
                    if (box.SelectedValue is JToken value)
                        Set(value.DeepClone(), true);
                };
                editors.Children.Add(box);
            }
            else if (isTable)
            {
                var rows = values[key] is JArray table ? (JArray)table.DeepClone() : [];
                editors.Children.Add(Table(rows, new[] { ("depth", "深度 mm", typeof(double)), ("thickness", "厚度 mm", typeof(double)), ("coverage", "覆盖率 %", typeof(double)), ("disconnect", "断开通孔", typeof(bool)) }, a => Set(a)));
            }
            else if (control is "number" or "integer" or "integer_spinbox")
            {
                var row = new Grid();
                row.ColumnDefinitions.Add(new() { Width = new GridLength(1, GridUnitType.Star) });
                var input = Numeric(values[key], control.StartsWith("integer"), f["unit"].Text(), n => Set(n), f["minimum"]?.Type is JTokenType.Integer or JTokenType.Float ? f["minimum"]!.Number() : 0, f["maximum"]?.Type is JTokenType.Integer or JTokenType.Float ? f["maximum"]!.Number() : null);
                row.Children.Add(input);
                string lo = f["minimum"]?.Type != JTokenType.Null ? f["minimum"].Text() : "0", hi = f["maximum"]?.Type != JTokenType.Null ? f["maximum"].Text() : "";
                var range = new TextBlock
                {
                    Text = hi == "" ? $"≥ {lo}" : $"{lo} – {hi}",
                    FontSize = 10,
                    Foreground = Brushes.SlateGray,
                    VerticalAlignment = VerticalAlignment.Center,
                    Margin = new(6, 0, 0, 0),
                    TextWrapping = TextWrapping.NoWrap,
                    TextTrimming = TextTrimming.CharacterEllipsis,
                    ToolTip = hi == "" ? $"≥ {lo}" : $"{lo} – {hi}"
                };
                editors.Children.Add(row);
                Grid.SetColumn(range, 2);
                host.Children.Add(range);
            }
            else
            {
                var box = new TextBox
                {
                    Text = values[key].Text()
                };
                box.TextChanged += (_, _) => Set(box.Text);
                editors.Children.Add(box);
            }

            if (f["help_text"].Text()is string help && help.Length > 0)
                editors.Children.Add(new TextBlock { Text = help, TextWrapping = TextWrapping.Wrap, Foreground = Brushes.SlateGray, FontSize = 11, Margin = new(0, 5, 0, 0) });
            FieldsPanel.Children.Add(host);
        }

        foreach (var f in fields.Where(f => !IsLocalGridField(f)))
            AddField(f);

        foreach (var s in workspace.Template.MaterialSelections.Where(s => s["step"].Text() == step && JsonData.Matches(s["visible_when"] as JObject, values)))
            AddMaterial(s);
        if (step == "bond_wires" && workspace.Document.TemplateId == "sop")
        {
            double Number(string key) => values[key].Number(double.NaN);
            double height = Number("die.thickness") + Number("die.attach") + Number("flag.thickness") - Number("leads.thickness") - Number("flag.downset");
            foreach (var(dimension, label)in new[]
            {
                ("length", "左右名义路径长度"),
                ("width", "上下名义路径长度")
            }

            )
            {
                double length = (Number("flag." + dimension) - Number("die." + dimension)) / 2 + Number("leads.gap") + Math.Abs(height);
                FieldsPanel.Children.Add(FieldRow(label + " (mm)", new TextBox { Text = double.IsFinite(length) ? length.ToString("G9", System.Globalization.CultureInfo.InvariantCulture) : "", IsReadOnly = true, Background = Brushes.WhiteSmoke }));
            }
        }

        if (step is "solder_balls" or "central_solder_balls" or "solder_removal")
            AddBga(step);
        if (step == "thermal_vias" && workspace.Document.TemplateId != "chip_array")
            AddViaConfiguration();
        if (step == "modeling")
            AddBgaModeling();
        foreach (var f in fields.Where(IsLocalGridField))
            AddField(f);
        if (FieldsPanel.Children.Count == 0)
            FieldsPanel.Children.Add(new TextBlock { Text = "当前封装配置未启用此组件。可在整体封装或基板步骤中调整组件选项。", TextWrapping = TextWrapping.Wrap, Foreground = Brushes.SlateGray, Margin = new(0, 8, 0, 14) });
        AlignFieldRows();
    }
}
