using System.Windows;
using System.Windows.Controls;
using HelixToolkit.Wpf;
using PackStudio.Core;
using PackStudio.Desktop;

namespace PackStudio.Desktop.Tests;
public static class Program
{
    [STAThread]
    public static int Main(string[] args)
    {
        bool configurationOnly = args.Contains("configuration", StringComparer.OrdinalIgnoreCase);
        var application = new Application();
        application.Resources.MergedDictionaries.Add(new ResourceDictionary { Source = new Uri("pack://application:,,,/PackStudio;component/DesktopResources.xaml") });
        var window = new MainWindow
        {
            ShowInTaskbar = false,
            ShowActivated = false,
            Opacity = 0
        };
        int failures = 0;
        window.Loaded += async (_, _) =>
        {
            try
            {
                var vm = (Workspace)window.DataContext;
                while (vm.IsBusy)
                    await Task.Delay(20);
                if (args.Contains("schematics", StringComparer.OrdinalIgnoreCase))
                {
                    SchematicChecks.Run(window, vm);
                    return;
                }
                await TemplateSelectionChecks.Run();
                DesLabelChecks.Run();
                NewPackageChecks.CancelPreservesProject(window, vm);
                var steps = (ListBox)window.FindName("StepList");
                var fields = (StackPanel)window.FindName("FieldsPanel");
                foreach (var family in vm.Catalog.Families)
                {
                    var created = await NewPackageChecks.CreateDraft(vm.Catalog, family.Id);
                    vm.Load(created);
                    if (steps.Items[0] is not WizardStep { Key: "summary" })
                        throw new Exception("summary must be first");
                    if (steps.Items.Cast<WizardStep>().Any(step => step.Key == "package_setup"))
                        throw new Exception("creation settings remain in navigation");
                    if (window.FindName("StepBox") != null || window.FindName("FamilyBox") != null || window.FindName("PresetBox") != null)
                        throw new Exception("sidebar still has creation/navigation dropdowns");
                    var keys = steps.Items.Cast<WizardStep>().Select(step => step.Key).ToList();
                    if (keys.Contains("solder_balls"))
                    {
                        int index = keys.IndexOf("solder_balls");
                        if (keys[index + 1] != "central_solder_balls" || keys[index + 2] != "solder_removal")
                            throw new Exception("BGA columns are not grouped in order");
                        steps.SelectedValue = "central_solder_balls";
                        var center = fields.Children.OfType<CheckBox>().Single(c => c.Content?.ToString() == "包含中央焊球");
                        bool initial = center.IsChecked == true;
                        center.IsChecked = !initial;
                        steps.SelectedValue = "solder_removal";
                        if (fields.Children.OfType<CheckBox>().Any(c => c.Content?.ToString() == "包含中央焊球") ||
                            !fields.Children.OfType<CheckBox>().Any(c => c.Content?.ToString() == "主阵列中心去球"))
                            throw new Exception("solder removal controls are misplaced");
                        steps.SelectedValue = "central_solder_balls";
                        center = fields.Children.OfType<CheckBox>().Single(c => c.Content?.ToString() == "包含中央焊球");
                        if (center.IsChecked != !initial) throw new Exception("BGA settings lost on navigation");
                        center.IsChecked = initial;
                    }
                    for (int i = 0; i < steps.Items.Count; i++)
                    {
                        steps.SelectedIndex = i;
                        window.UpdateLayout();
                        if (fields.Children.Count == 0)
                            throw new Exception(family.Id + " empty wizard step " + i);
                        foreach (var row in fields.Children.OfType<Grid>().Where(r => r.Visibility == Visibility.Visible))
                        {
                            FrameworkElement? label = row.Children.OfType<DockPanel>().FirstOrDefault() ?? (FrameworkElement?)row.Children.OfType<TextBlock>().FirstOrDefault();
                            if (label is not TextBlock && label is not DockPanel) continue;
                            var text = label is TextBlock block ? block : ((DockPanel)label).Children.OfType<TextBlock>().LastOrDefault();
                            if (text == null || string.IsNullOrEmpty(text.Text)) continue;
                            var measured = new TextBlock { Text = text.Text, FontFamily = text.FontFamily, FontSize = text.FontSize, FontWeight = text.FontWeight };
                            measured.Measure(new Size(double.PositiveInfinity, double.PositiveInfinity));
                            if (text.ActualWidth + 1 < measured.DesiredSize.Width)
                                throw new Exception($"{family.Id} label is truncated: {text.Text} ({text.ActualWidth:F1} < {measured.DesiredSize.Width:F1})");
                        }
                    }

                    ModelingStepChecks.Run(window, steps, fields, vm);
                    ParameterFormChecks.Run(window, vm, steps, fields);
                    SemanticFieldChecks.Run(window, vm, steps, fields);
                    FieldLayoutChecks.Run(window, steps, fields, vm);
                    RemovalMatrixChecks.Run(window, steps, fields, vm);
                    await TableEditorChecks.Run(window, steps, fields, vm);
                    if (family.Id == "bare_die")
                    {
                        steps.SelectedValue = "bumped_die";
                        var check = fields.Children.OfType<Grid>().SelectMany(row => row.Children.OfType<StackPanel>()).SelectMany(panel => panel.Children.OfType<CheckBox>()).First();
                        if (check.Content?.ToString() != "包含凸点与底填充" || Grid.GetColumnSpan((StackPanel)check.Parent) != 3)
                            throw new Exception("checkbox label is not displayed on one row");
                    }
                    if (family.Id == "pbga_wb")
                    {
                        steps.SelectedValue = "die";
                        bool hasLw = fields.Children.OfType<Grid>().SelectMany(row => row.Children.OfType<DockPanel>()).SelectMany(panel => panel.Children.OfType<TextBlock>()).Any(text => text.Text.Trim() == "Lw");
                        if (!hasLw) throw new Exception("DES symbol Lw is missing");
                    }
                    await vm.GenerateAsync();
                    if (!vm.IsCurrent || vm.Model == null)
                        throw new Exception(family.Id + ": " + vm.Status + Environment.NewLine + string.Join(Environment.NewLine, vm.Issues.Select(i => i.Code + ": " + i.Message)));
                    var viewport = (HelixViewport3D)window.FindName("Viewport");
                    if (viewport.Children.Count != vm.Model.Blocks.Count + 1)
                        throw new Exception("preview block count");
                    if (!configurationOnly)
                    {
                        WorkspaceChecks.CheckModelRoot(window);
                        ModelTreeChecks.Run(window, vm);
                    }
                    vm.ChangeVisibility(vm.Model.Blocks.Select(b => b.Id), false);
                    if (viewport.Children.Count != 1)
                        throw new Exception("hidden blocks remain in preview");
                    if (ModelXmlExporter.Export(vm.Result!).Descendants("block").Count() != vm.Model.Blocks.Count)
                        throw new Exception("visibility changed export");
                    vm.ChangeVisibility(vm.Model.Blocks.Select(b => b.Id), true);
                    var materials = new MaterialWindow(vm)
                    {
                        ShowInTaskbar = false,
                        ShowActivated = false,
                        Opacity = 0
                    };
                    materials.Show();
                    materials.Close();
                    Console.WriteLine("PASS desktop " + family.Id);
                }

                TableEditorChecks.Verify();

                await NewPackageChecks.FinishCreatesProject(window, vm);
                await ParameterFormChecks.ValidationAsync(window, vm);
                if (!configurationOnly)
                {
                    WorkspaceChecks.Run(window, vm);
                    await ViewportScaleChecks.Run(window);
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine(ex);
                failures++;
            }
            finally
            {
                application.Shutdown(failures == 0 ? 0 : 1);
            }
        };
        return application.Run(window);
    }
}
