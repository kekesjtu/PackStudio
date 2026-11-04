using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Data;
using System.Windows.Media;
using PackStudio.Core;
using PackStudio.Desktop;

namespace PackStudio.Desktop.Tests;

static class ParameterFormChecks
{
    public static void Run(MainWindow window, Workspace workspace, ListBox steps, StackPanel panel)
    {
        steps.SelectedValue = "modeling";
        window.UpdateLayout();
        var grid = Descendants<CheckBox>(panel).Single(b => b.Content?.ToString() == "局部网格");
        var density = Descendants<ComboBox>(panel).Single(b => BindingOperations.GetBindingExpression(b, Selector.SelectedValueProperty)?.ParentBinding.Source is ParameterField { Key: "grid.density" });
        bool original = grid.IsChecked == true;
        grid.IsChecked = false;
        window.UpdateLayout();
        if (workspace.Document.Values["grid.enabled"].Flag() || Descendants<ComboBox>(panel).Contains(density))
            throw new Exception("field binding did not hide disabled grid settings");
        grid.IsChecked = true;
        window.UpdateLayout();
        if (!workspace.Document.Values["grid.enabled"].Flag() || !Descendants<ComboBox>(panel).Contains(density))
            throw new Exception("field visibility binding did not restore grid settings");
        grid.IsChecked = original;
        var form = new ParameterForm(workspace);
        var power = form.Fields.Single(f => f.Key == "die.power");
        string savedPower = power.TextValue;
        power.TextValue = "1.";
        int unrelatedNotifications = 0, densityChanges = 0;
        power.PropertyChanged += (_, _) => unrelatedNotifications++;
        form.Fields.Single(f => f.Key == "grid.density").PropertyChanged += (_, e) => { if (e.PropertyName == nameof(ParameterField.Visible)) densityChanges++; };
        var enabled = form.Fields.Single(f => f.Key == "grid.enabled");
        enabled.BooleanValue = !original;
        if (unrelatedNotifications != 0 || densityChanges != 1 || power.TextValue != "1.")
            throw new Exception("field dependency propagation touched unrelated input");
        enabled.BooleanValue = original;
        power.TextValue = savedPower;
    }

    public static async Task ValidationAsync(MainWindow window, Workspace workspace)
    {
        var form = new ParameterForm(workspace);
        var length = form.Fields.Single(f => f.Key == "die.length");
        string original = length.TextValue;
        length.TextValue = "-1";
        if (length.HasError || workspace.CanExport) throw new Exception("editing validated input or allowed stale export");
        await workspace.GenerateAsync();
        var issue = workspace.Issues.FirstOrDefault(i => i.Severity == IssueSeverity.Error && i.ParameterPaths.Contains("die.length"));
        if (issue == null || workspace.Model != null || workspace.CanExport || !length.HasError)
            throw new Exception("invalid input did not produce a structured blocking field issue");
        var issues = (ListBox)window.FindName("IssuesList");
        if (!issues.IsHitTestVisible) throw new Exception("issue list cannot receive clicks");
        issues.SelectedItem = issue;
        var steps = (ListBox)window.FindName("StepList");
        if (steps.SelectedValue?.ToString() != length.Step || length.TextValue != "-1")
            throw new Exception("issue navigation changed input or did not locate its parameter step");
        length.TextValue = original;
        await workspace.GenerateAsync();
        if (!workspace.CanExport) throw new Exception("corrected input did not restore export");
        var overlap = workspace.Issues.FirstOrDefault(i => i.EntityIds.Count == 2);
        if (overlap != null)
        {
            issues.SelectedItem = overlap;
            if (!workspace.Selected.SetEquals(overlap.EntityIds) || overlap.EntityIds.Any(workspace.Hidden.Contains))
                throw new Exception("geometry issue did not highlight its affected pair");
            workspace.ClearSelection();
        }
        Console.WriteLine("PASS validation stages, issue navigation, geometry selection and export gating");
    }

    static IEnumerable<T> Descendants<T>(DependencyObject root) where T : DependencyObject
    {
        if (root is UIElement { Visibility: not Visibility.Visible }) yield break;
        for (int i = 0; i < VisualTreeHelper.GetChildrenCount(root); i++)
        {
            var child = VisualTreeHelper.GetChild(root, i);
            if (child is UIElement { Visibility: not Visibility.Visible }) continue;
            if (child is T match) yield return match;
            foreach (var nested in Descendants<T>(child)) yield return nested;
        }
    }
}
