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
        var fields = form.Fields.Where(f => f.Step == step && f.Type != "footprint").ToList();
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

    ParameterField? Find(string path) => path.StartsWith("MaterialAssignments.")
        ? form.Materials.FirstOrDefault(f => f.Key == "$material:" + path["MaterialAssignments.".Length..])
        : form.Fields.FirstOrDefault(f => f.ContainsPath(path));
    public string? StepFor(string path) => path == "Name" ? "summary" : Find(path)?.Step;

    public void Focus(string path)
    {
        if (path == "Name")
        {
            Descendants(FieldsPanel).OfType<TextBox>().FirstOrDefault()?.Focus();
            return;
        }
        if (Find(path) is not { } field) return;
        var view = FieldsPanel.Children.OfType<FrameworkElement>().FirstOrDefault(v => v.DataContext == field);
        if (view == null) return;
        view.BringIntoView();
        var children = Descendants(view).ToList();
        if (children.OfType<DataGrid>().FirstOrDefault() is { } table)
        {
            var parts = path[field.Key.Length..].Replace("].", "/").Replace("[", "/").Replace("]", "").Trim('/').Split('/');
            if (parts.Length > 0 && int.TryParse(parts[0], out int index) && index >= 0 && index < table.Items.Count)
            {
                table.SelectedIndex = index;
                var column = parts.Length > 1 ? table.Columns.FirstOrDefault(c => c.SortMemberPath == parts[1]) : table.Columns.FirstOrDefault();
                table.ScrollIntoView(table.SelectedItem, column);
                if (column != null) table.CurrentCell = new(table.SelectedItem, column);
            }
            table.Focus();
        }
        else children.OfType<Control>().FirstOrDefault(c => c.Focusable)?.Focus();
    }

    static IEnumerable<DependencyObject> Descendants(DependencyObject view)
    {
        for (int i = 0; i < VisualTreeHelper.GetChildrenCount(view); i++)
        {
            var child = VisualTreeHelper.GetChild(view, i);
            yield return child;
            foreach (var nested in Descendants(child)) yield return nested;
        }
    }
}
