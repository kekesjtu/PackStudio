using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Media;
using PackStudio.Core;

namespace PackStudio.Desktop;

public sealed partial class ParameterPanel
{
    readonly Workspace workspace;
    readonly StackPanel FieldsPanel;
    ParameterForm form = null!;
    public event Action? Changed;
    public ParameterPanel(Workspace workspace, StackPanel panel)
    {
        this.workspace = workspace; FieldsPanel = panel;
        Grid.SetIsSharedSizeScope(panel, true);
    }
    void FormChanged() => Changed?.Invoke();
    public void Reset()
    {
        if (form != null) form.Changed -= FormChanged;
        form = new(workspace);
        form.Changed += FormChanged;
    }
    public void Show(string step)
    {
        FieldsPanel.Children.Clear();
        if (step == "summary") { AddSummary(); return; }
        var fields = form.Fields.Where(f => f.Step == step && f.Control is not ("footprint" or "hidden")).ToList();
        var materials = form.Materials.Where(f => f.Step == step).ToList();
        bool Footer(ParameterField f) => f.Definition["placement"].Text() == "footer";
        foreach (var field in fields.Where(f => !Footer(f))) FieldsPanel.Children.Add(FieldView.Create(field));
        foreach (var material in materials) AddMaterial(material);
        foreach (var field in fields.Where(Footer)) FieldsPanel.Children.Add(FieldView.Create(field));
        var empty = new TextBlock { Text = "当前封装配置未启用此组件。", TextWrapping = TextWrapping.Wrap, Foreground = Brushes.SlateGray, Margin = new(0, 8, 0, 14) };
        var visibility = new MultiBinding { Converter = new EmptySectionVisibility() };
        foreach (var field in fields.Concat(materials)) visibility.Bindings.Add(new Binding(nameof(ParameterField.Visible)) { Source = field });
        empty.SetBinding(UIElement.VisibilityProperty, visibility);
        FieldsPanel.Children.Add(empty);
    }
}
