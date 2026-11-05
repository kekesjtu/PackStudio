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
            var draft = new NewPackageViewModel(workspace.Template, workspace.Template.DefaultPreset);
            var creation = new ParameterForm(draft);
            var top = creation.Fields.Single(f => f.Key == "trace.top_thickness");
            top.TextValue = "-0.025";
            if (top.HasError || PackageInitializer.Create(workspace.Template, draft.PresetId, "thickness", draft.Overrides).Values["trace.top_thickness"]!.Number() != -0.025)
                throw new Exception("creation constrained or rejected a submitted negative value");
            top.TextValue = "0.025";
            if (Math.Abs(PackageInitializer.Create(workspace.Template, draft.PresetId, "thickness", draft.Overrides).Values["metal.layers"]![0]!["thickness"].Number() - 0.025) > 1e-10)
                throw new Exception("creation-only input no longer initializes table");
        }
        steps.SelectedValue = "summary";
        window.UpdateLayout();
        var rows = panel.Children.OfType<Grid>().Where(r => r.Visibility == Visibility.Visible).ToList();
        if (rows.Count != 2 || !rows.Select(r => r.Children.OfType<TextBlock>().First().Text).SequenceEqual(new[] { "设计名称", "封装类型" }))
            throw new Exception("summary must show only design name and package type");
        var name = rows[0].Children.OfType<TextBox>().Single();
        if (name.Text != workspace.DesignName || name.MaxLength != 160)
            throw new Exception("summary name or length limit is incorrect");
        if (rows[1].Children.OfType<TextBlock>().Last().Text != workspace.Template.Info.Name)
            throw new Exception("summary package type is incorrect");
        string original = workspace.DesignName;
        long revision = workspace.Revision;
        name.Text = "概要编辑名称";
        if (workspace.DesignName != name.Text || workspace.Revision != revision + 1 || !window.Title.StartsWith(name.Text))
            throw new Exception("summary name edit did not update document and title once");
        workspace.Rename(original);
        if (name.Text != original) throw new Exception("summary name did not follow document rename");
    }
}
