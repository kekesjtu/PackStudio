using System.Windows;
using System.Windows.Controls;
using HelixToolkit.Wpf;
using PackStudio.Core;
using PackStudio.Desktop;

namespace PackStudio.Desktop.Tests;
public static class Program
{
    [STAThread]
    public static int Main()
    {
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
                NewPackageChecks.CancelPreservesProject(window, vm);
                var steps = (ListBox)window.FindName("StepList");
                var fields = (StackPanel)window.FindName("FieldsPanel");
                foreach (var family in PackageCatalog.Families)
                {
                    var created = NewPackageChecks.CreateDraft(vm.Catalog, family.Id);
                    vm.Load(created);
                    if (steps.Items[0] is not WizardStep { Key: "summary" })
                        throw new Exception("summary must be first");
                    if (steps.Items.Cast<WizardStep>().Any(step => step.Key == "package_setup"))
                        throw new Exception("creation settings remain in navigation");
                    if (window.FindName("StepBox") != null || window.FindName("FamilyBox") != null || window.FindName("PresetBox") != null)
                        throw new Exception("sidebar still has creation/navigation dropdowns");
                    for (int i = 0; i < steps.Items.Count; i++)
                    {
                        steps.SelectedIndex = i;
                        window.UpdateLayout();
                        if (fields.Children.Count == 0)
                            throw new Exception(family.Id + " empty wizard step " + i);
                    }

                    await vm.GenerateAsync();
                    if (!vm.IsCurrent || vm.Model == null)
                        throw new Exception(family.Id + ": " + vm.Status);
                    var viewport = (HelixViewport3D)window.FindName("Viewport");
                    if (viewport.Children.Count != vm.Model.Blocks.Count + 1)
                        throw new Exception("preview block count");
                    WorkspaceChecks.CheckModelRoot(window);
                    ModelTreeChecks.Run(window, vm);
                    vm.ChangeVisibility(vm.Model.Blocks.Select(b => b.Id), false);
                    if (viewport.Children.Count != 1)
                        throw new Exception("hidden blocks remain in preview");
                    if (FloXml.Export(vm.Model).Descendants("cuboid").Count() != vm.Model.Blocks.Count)
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

                await NewPackageChecks.FinishCreatesProject(window, vm);
                WorkspaceChecks.Run(window, vm);
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
