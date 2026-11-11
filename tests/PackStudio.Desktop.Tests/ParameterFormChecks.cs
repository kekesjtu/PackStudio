using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Data;
using System.Windows.Media;
using Newtonsoft.Json.Linq;
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
        if (workspace.Document.TemplateId is "cbga_fc" or "pbga_fc")
            CheckSlugCoverSwitch(form);
        if (form.Fields.Any(f => f.Key == "bga.ball_map_enabled"))
            CheckBgaLayout(window, workspace, steps, panel);
    }

    static void CheckBgaLayout(MainWindow window, Workspace workspace, ListBox steps, StackPanel panel)
    {
        steps.SelectedValue = "modeling";
        window.UpdateLayout();
        var representation = (ParameterField)Descendants<ComboBox>(panel).Single(box => box.DataContext is ParameterField { Key: "bga.representation" }).DataContext;
        var originalRepresentation = representation.Value!.DeepClone();
        var equivalent = representation.Options.FirstOrDefault(option => option["value"].Text() != "discrete")?["value"] ?? new JValue("discrete");
        steps.SelectedValue = "solder_balls";
        window.UpdateLayout();
        var mapToggle = Descendants<CheckBox>(panel).Single(box => box.DataContext is ParameterField { Key: "bga.ball_map_enabled" });
        bool originalMapEnabled = mapToggle.IsChecked == true;
        mapToggle.IsChecked = false;
        var mapView = panel.Children.OfType<FrameworkElement>().Single(view => view.DataContext is ParameterField { Key: "bga.ball_map" });
        var mapField = (ParameterField)mapView.DataContext;
        var originalMap = mapField.Value!.DeepClone();
        window.UpdateLayout();
        if (mapView.Visibility != Visibility.Collapsed) throw new Exception("unchecked Ball Map table is still displayed");
        representation.ChoiceValue = equivalent;
        mapToggle.IsChecked = true;
        window.UpdateLayout();
        if (!mapView.IsVisible || representation.Value.Text() != "discrete" || representation.Enabled ||
            equivalent.Text() != "discrete" && !workspace.Status.Contains("discrete"))
            throw new Exception("enabling Ball Map did not display its table, switch representation and notify the user");
        representation.ChoiceValue = equivalent;
        if (representation.Value.Text() != "discrete" || string.IsNullOrEmpty(((ParameterField)mapToggle.DataContext).Notice))
            throw new Exception("active Ball Map allowed equivalent modeling or lost its persistent notice");
        if (workspace.Document.TemplateId == "pbga_fc") NewPackageChecks.Capture(window, "bga-ball-map-enabled.png");
        mapField.Set(new JArray(new JObject { ["id"] = "A1", ["x"] = 0, ["y"] = 0 }));
        mapToggle.IsChecked = false;
        mapToggle.IsChecked = true;
        if (mapField.Value![0]!["id"].Text() != "A1") throw new Exception("Ball Map toggle discarded coordinates");
        mapToggle.IsChecked = false;
        mapField.Set(originalMap);

        steps.SelectedValue = "solder_removal";
        window.UpdateLayout();
        var center = Descendants<CheckBox>(panel).Single(box => box.DataContext is ParameterField { Key: "bga.solder_removal_enabled" });
        var explicitToggle = Descendants<CheckBox>(panel).Single(box => box.DataContext is ParameterField { Key: "bga.omitted_cells" });
        var explicitField = (ParameterField)explicitToggle.DataContext;
        bool originalCenter = center.IsChecked == true, originalEnabled = explicitField.MatrixEnabled;
        center.IsChecked = false;
        explicitToggle.IsChecked = false;
        representation.ChoiceValue = equivalent;
        var originalCells = explicitField.Value!.DeepClone();
        explicitToggle.IsChecked = true;
        window.UpdateLayout();
        if (center.IsChecked != false || representation.Value.Text() != "discrete" || representation.Enabled || explicitField.Notice.Length == 0 ||
            equivalent.Text() != "discrete" && !workspace.Status.Contains("discrete"))
            throw new Exception("explicit removal did not independently switch representation and notify the user");
        if (workspace.Document.TemplateId == "pbga_fc") NewPackageChecks.Capture(window, "bga-explicit-discrete.png");
        long revision = workspace.Revision;
        explicitToggle.IsChecked = false;
        if (workspace.Revision != revision + 1 || !JToken.DeepEquals(originalCells, explicitField.Value) ||
            workspace.Document.Values["bga.explicit_removal_enabled"].Flag() || !representation.Enabled)
            throw new Exception("disabling explicit removal did not persist its state, preserve selection and unlock representation");
        explicitToggle.IsChecked = true;
        mapToggle.IsChecked = true;
        explicitToggle.IsChecked = false;
        if (representation.Enabled) throw new Exception("representation unlocked while Ball Map was still active");
        mapToggle.IsChecked = false;
        if (!representation.Enabled) throw new Exception("representation remained locked after both features were disabled");
        explicitToggle.IsChecked = originalEnabled;
        center.IsChecked = originalCenter;
        mapToggle.IsChecked = originalMapEnabled;
        representation.ChoiceValue = originalRepresentation;
        var imported = workspace.Document.Clone();
        imported.Values["bga.explicit_removal_enabled"] = true;
        imported.Values["bga.representation"] = equivalent.DeepClone();
        var importedWorkspace = new Workspace();
        importedWorkspace.Load(imported);
        var importedForm = new ParameterForm(importedWorkspace);
        if (importedWorkspace.Document.Values["bga.representation"].Text() != "discrete" ||
            importedForm.Fields.Single(field => field.Key == "bga.representation").Enabled)
            throw new Exception("opening enabled explicit removal did not normalize and lock its representation");
        if (equivalent.Text() != "discrete" && !importedWorkspace.Status.Contains("discrete"))
            throw new Exception("opening conflicting BGA settings silently changed representation");
        Console.WriteLine("PASS " + workspace.Document.TemplateId + " BGA enable switches, discrete lock and persistent notice");
    }

    static void CheckSlugCoverSwitch(ParameterForm form)
    {
        var cover = form.Fields.Single(f => f.Key == "cover.type");
        var slug = form.Fields.Single(f => f.Key == "slug.enabled");
        var length = form.Fields.Single(f => f.Key == "slug.length");
        var originalCover = cover.Value!.DeepClone();
        var originalLength = length.Value?.DeepClone() ?? JValue.CreateNull();
        bool originalSlug = slug.BooleanValue;
        var box = Descendants<CheckBox>(FieldView.Create(slug)).Single();

        cover.ChoiceValue = new JValue("encapsulant");
        box.IsChecked = true;
        length.Set(new JValue(3.5));
        cover.ChoiceValue = new JValue("lid");
        if (box.IsChecked != false || box.IsEnabled || slug.BooleanValue || length.Visible)
            throw new Exception("leaving encapsulant did not clear and disable the slug checkbox");

        cover.ChoiceValue = new JValue("encapsulant");
        if (box.IsChecked != false || !box.IsEnabled || length.Visible)
            throw new Exception("returning to encapsulant did not leave the slug off and available");
        box.IsChecked = true;
        if (!length.Visible || length.Value.Number() != 3.5)
            throw new Exception("re-enabling slug did not restore its edited parameters");

        cover.ChoiceValue = originalCover;
        slug.BooleanValue = originalSlug;
        length.Set(originalLength);
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
        window.UpdateLayout();
        if (issues.Visibility != Visibility.Visible) throw new Exception("errors did not expand the issue list");
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
