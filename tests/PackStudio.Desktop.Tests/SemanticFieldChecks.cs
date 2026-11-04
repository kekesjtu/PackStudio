using System.Windows;
using System.Windows.Controls;
using PackStudio.Core;
using PackStudio.Desktop;

namespace PackStudio.Desktop.Tests;

static class SemanticFieldChecks
{
    public static void Run(MainWindow window, Workspace workspace, ListBox steps, StackPanel panel)
    {
        var form = new ParameterForm(workspace);
        if (form.Fields.Any(f => f.Definition["creation_only"].Flag())) throw new Exception("creation-only fields remain in modeling form");
        if (workspace.Template.CreationFields.Any(f => f["creation_only"].Flag()))
        {
            var draft = new CreationDraft(workspace.Template, workspace.Document.PresetId);
            var creation = new ParameterForm(draft);
            var top = creation.Fields.Single(f => f.Key == "trace.top_thickness");
            top.TextValue = "0.025";
            if (Math.Abs(draft.Complete("thickness").Values["metal.layers"]![0]!["thickness"].Number() - 0.025) > 1e-10)
                throw new Exception("creation-only input no longer initializes table");
        }
        steps.SelectedValue = "summary";
        window.UpdateLayout();
        var rows = panel.Children.OfType<Grid>().Where(r => r.Visibility == Visibility.Visible).ToList();
        if (rows.Any(r => r.DataContext is not SummaryField)) throw new Exception("summary bypasses declared fields");
        var name = rows.Single(r => r.DataContext is SummaryField { Editable: true }).Children.OfType<TextBox>().Single();
        string original = workspace.DesignName;
        name.Text = "概要编辑名称";
        if (workspace.DesignName != name.Text) throw new Exception("summary name binding did not update document");
        name.Text = original;

        var definitions = workspace.Template.Steps.Single(s => s["key"].Text() == "summary")["fields"]!;
        var powerDefinition = definitions.Single(f => f["parameter"].Text() == "die.power");
        var powerSummary = new SummaryField(workspace, form, powerDefinition);
        var power = form.Fields.Single(f => f.Key == "die.power");
        string saved = power.TextValue;
        int changes = 0;
        powerSummary.PropertyChanged += (_, e) => { if (e.PropertyName == nameof(SummaryField.Text)) changes++; };
        power.TextValue = "7.25";
        if (powerSummary.Text != "7.25 W" || changes == 0) throw new Exception("summary format or source binding failed");
        power.TextValue = saved;
        var layers = rows.Select(r => (SummaryField)r.DataContext).Any(f => f.Label == "基板层数");
        if (layers != workspace.Document.Values.ContainsKey("substrate.layers")) throw new Exception("summary empty-source visibility failed");
    }
}
