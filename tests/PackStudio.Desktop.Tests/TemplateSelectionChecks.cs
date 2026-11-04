using System.Diagnostics;
using System.Reflection;
using System.Windows;
using System.Windows.Controls;
using PackStudio.Core;
using PackStudio.Desktop;

namespace PackStudio.Desktop.Tests;

static class TemplateSelectionChecks
{
    static void Require(bool success, string message)
    {
        if (!success) throw new Exception(message);
    }

    public static async Task Run()
    {
        var catalog = new PackageCatalog(App.DataRoot);
        var dialog = new NewPackageWindow(catalog) { Opacity = 0, ShowActivated = false, ShowInTaskbar = false };
        dialog.Show();
        try
        {
            var list = (ListBox)dialog.FindName("TemplateList");
            var draft = dialog.Draft;
            var watch = Stopwatch.StartNew();
            for (int i = 0; i < 80; i++)
            {
                string id = catalog.Families[i % catalog.Families.Count].Id;
                list.SelectedValue = id;
                Require(list.SelectedItem is TemplateInfo choice && choice.Id == id, "template selection lagged behind input");
                Require(ReferenceEquals(draft, dialog.Draft), "template picking rebuilt the draft before Next");
            }
            Console.WriteLine($"PASS 80 rapid template selections in {watch.Elapsed.TotalMilliseconds:F1} ms");
            Require(((StackPanel)dialog.FindName("CreationOptions")).Children.Count == 0, "hidden options built during template picking");
            list.SelectedValue = "qfn";
            await NewPackageChecks.OpenCustomize(dialog);
            Require(dialog.Draft!.Template.Info.Id == "qfn", "Next did not load the final selection");
            ((Button)dialog.FindName("BackButton")).RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
            list.SelectedValue = "sop";
            list.SelectedValue = "pqfp";
            await NewPackageChecks.OpenCustomize(dialog);
            Require(dialog.Draft!.Template.Info.Id == "pqfp", "changing template after Back loaded stale data");
        }
        finally { dialog.Close(); }

        // A cold family load is still running when the dialog closes.
        var canceled = new NewPackageWindow(new PackageCatalog(App.DataRoot), "pbga_wb")
            { Opacity = 0, ShowActivated = false, ShowInTaskbar = false };
        canceled.Show();
        var initial = canceled.Draft;
        var prepare = (Task<bool>)typeof(NewPackageWindow).GetMethod("PrepareTemplateAsync", BindingFlags.NonPublic | BindingFlags.Instance)!.Invoke(canceled, null)!;
        canceled.Close();
        Require(!await prepare && ReferenceEquals(initial, canceled.Draft) && canceled.CreatedDocument == null,
            "closing during load applied a draft to the closed dialog");
        Console.WriteLine("PASS final template initialization and cancellation during loading");
    }
}
