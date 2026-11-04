using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Media;
using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;

public sealed partial class ParameterPanel
{
    readonly Workspace workspace;
    readonly StackPanel FieldsPanel;
    ParameterForm form = null!;
    readonly List<(FrameworkElement View, Func<bool> Visible)> rows = [];
    readonly TextBlock empty = new() { Text = "当前封装配置未启用此组件。", TextWrapping = TextWrapping.Wrap, Foreground = Brushes.SlateGray, Margin = new(0, 8, 0, 14) };
    public event Action? Changed;

    public ParameterPanel(Workspace workspace, StackPanel panel)
    {
        this.workspace = workspace;
        FieldsPanel = panel;
    }

    public void Reset()
    {
        if (form != null) form.Changed -= UpdateVisibility;
        form = new(workspace);
        form.Changed += UpdateVisibility;
    }

    public void Show(string step)
    {
        FieldsPanel.Children.Clear();
        rows.Clear();
        if (step == "summary")
        {
            AddSummary();
            AlignFieldRows();
            return;
        }
        var fields = form.Fields.Where(f => f.Step == step && f.Control is not ("footprint" or "hidden")).ToList();
        bool GridField(ParameterField f) => f.Key.StartsWith("grid.", StringComparison.Ordinal) || f.Key.Contains(".grid.", StringComparison.Ordinal);
        foreach (var field in fields.Where(f => !GridField(f))) AddField(field);
        foreach (var selection in workspace.Template.MaterialSelections.Where(s => s["step"].Text() == step))
        {
            int start = FieldsPanel.Children.Count;
            AddMaterial(selection);
            foreach (var view in FieldsPanel.Children.OfType<FrameworkElement>().Skip(start))
                rows.Add((view, () => JsonData.Matches(selection["visible_when"] as JObject, form.Values)));
        }
        foreach (var field in fields.Where(GridField)) AddField(field);
        UpdateVisibility();
    }

    void AddField(ParameterField field)
    {
        var f = field.Definition;
        string control = field.Control;
        if (control == "removal_matrix")
        {
            var box = new CheckBox { Content = field.Label, Margin = new(0, 10, 0, 5) };
            Bind(box, CheckBox.IsCheckedProperty, field, nameof(ParameterField.Expanded));
            Register(box, () => field.Visible);
            Register(new RemovalMatrixEditor(field), () => field.Visible && field.Expanded);
            return;
        }
        var editors = new StackPanel();
        string symbol = control is "number" or "integer" or "integer_spinbox" ? DesFieldLabels.Symbol(f, form.Values["substrate.layers"].Text()) : "";
        var host = FieldRow(field.Label, editors, symbol);
        Bind(host, UIElement.IsEnabledProperty, field, nameof(ParameterField.Enabled), BindingMode.OneWay);
        if (control == "checkbox")
        {
            var box = new CheckBox { Content = field.Label, ToolTip = field.Label };
            Bind(box, CheckBox.IsCheckedProperty, field, nameof(ParameterField.BooleanValue));
            if (f["standalone"].Flag()) { Register(box, () => field.Visible); return; }
            host.Children.RemoveAt(0);
            Grid.SetColumn(editors, 0);
            Grid.SetColumnSpan(editors, 3);
            editors.Children.Add(box);
        }
        else if (f["options"] is JArray { Count: > 0 } options)
        {
            var box = new ComboBox
            {
                ItemsSource = options.Select(o => new { Value = o.DeepClone(), Label = f["option_labels"]?[o.ToString()].Text(o.ToString()) ?? o.ToString() }).ToList(),
                DisplayMemberPath = "Label", SelectedValuePath = "Value"
            };
            Bind(box, ComboBox.SelectedValueProperty, field, nameof(ParameterField.ChoiceValue));
            editors.Children.Add(box);
        }
        else if (control == "table")
        {
            host.RowDefinitions.Add(new() { Height = GridLength.Auto });
            host.RowDefinitions.Add(new() { Height = GridLength.Auto });
            Grid.SetColumnSpan(host.Children[0], 3);
            ((TextBlock)host.Children[0]).HorizontalAlignment = HorizontalAlignment.Left;
            Grid.SetColumn(editors, 0);
            Grid.SetColumnSpan(editors, 3);
            Grid.SetRow(editors, 1);
            editors.Margin = new(0, 6, 0, 0);
            var columns = ((JArray)f["columns"]!).Select(c => (c["key"].Text(), c["label"].Text(), c["type"].Text() switch { "checkbox" => typeof(bool), "text" => typeof(string), _ => typeof(double) })).ToArray();
            editors.Children.Add(Table(field.Value is JArray table ? (JArray)table.DeepClone() : [], columns, field.Set));
        }
        else if (control is "number" or "integer" or "integer_spinbox")
        {
            double minimum = f["minimum"]?.Type is JTokenType.Integer or JTokenType.Float ? f["minimum"]!.Number() : 0;
            double? maximum = f["maximum"]?.Type is JTokenType.Integer or JTokenType.Float ? f["maximum"]!.Number() : null;
            var input = Numeric(field.Value, control.StartsWith("integer"), f["unit"].Text(), _ => { }, minimum, maximum);
            var text = ((DockPanel)((Border)input).Child).Children.OfType<TextBox>().Single();
            Bind(text, TextBox.TextProperty, field, nameof(ParameterField.TextValue));
            editors.Children.Add(input);
            string range = maximum.HasValue ? $"{minimum} – {maximum}" : $"≥ {minimum}";
            var hint = new TextBlock { Text = range, ToolTip = range, FontSize = 10, Foreground = Brushes.SlateGray, VerticalAlignment = VerticalAlignment.Center, Margin = new(6, 0, 0, 0), TextTrimming = TextTrimming.CharacterEllipsis };
            Grid.SetColumn(hint, 2);
            host.Children.Add(hint);
        }
        else
        {
            var text = new TextBox { IsReadOnly = control == "derived" };
            Bind(text, TextBox.TextProperty, field, control == "derived" ? nameof(ParameterField.DerivedValue) : nameof(ParameterField.TextValue), control == "derived" ? BindingMode.OneWay : BindingMode.TwoWay);
            editors.Children.Add(text);
        }
        if (f["help_text"].Text() is string help && help.Length > 0)
            editors.Children.Add(new TextBlock { Text = help, TextWrapping = TextWrapping.Wrap, Foreground = Brushes.SlateGray, FontSize = 11 });
        Register(host, () => field.Visible);
    }

    static void Bind(FrameworkElement view, DependencyProperty property, ParameterField field, string name, BindingMode mode = BindingMode.TwoWay) =>
        view.SetBinding(property, new Binding(name) { Source = field, Mode = mode, UpdateSourceTrigger = UpdateSourceTrigger.PropertyChanged });

    void Register(FrameworkElement view, Func<bool> visible)
    {
        rows.Add((view, visible));
        FieldsPanel.Children.Add(view);
    }

    void UpdateVisibility()
    {
        var visible = rows.Where(row => row.Visible()).Select(row => row.View).ToList();
        foreach (var view in FieldsPanel.Children.OfType<FrameworkElement>().Where(view => !visible.Contains(view)).ToList())
            FieldsPanel.Children.Remove(view);
        for (int i = 0; i < visible.Count; i++)
            if (!FieldsPanel.Children.Contains(visible[i])) FieldsPanel.Children.Insert(i, visible[i]);
        if (visible.Count == 0) FieldsPanel.Children.Add(empty);
        AlignFieldRows();
        Changed?.Invoke();
    }
}
