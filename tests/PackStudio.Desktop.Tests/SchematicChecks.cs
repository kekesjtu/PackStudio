using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using AvalonDock.Layout;
using PackStudio.Core;
using PackStudio.Desktop;

namespace PackStudio.Desktop.Tests;

static class SchematicChecks
{
    public static void Run(MainWindow window, Workspace workspace)
    {
        var steps = (ListBox)window.FindName("StepList");
        var schematic = (PackageSchematic)window.FindName("Schematic");
        var modelTab = (LayoutDocument)window.FindName("ModelDocument");
        var diagramTab = (LayoutDocument)window.FindName("SchematicDocument");
        Require(ReferenceEquals(modelTab.Parent, diagramTab.Parent), "示意图与三维模型必须是同级标签页");
        int count = 0, modelingCount = 0;
        var previews = new HashSet<string>();
        foreach (var family in PackageCatalog.Families)
        {
            workspace.Select(family.Id);
            foreach (var item in steps.Items.Cast<WizardStep>())
            {
                // Ensure SelectionChanged fires even for the initially selected summary.
                steps.SelectedIndex = -1;
                modelTab.IsSelected = true;
                steps.SelectedValue = item.Key;
                steps.ScrollIntoView(item);
                window.UpdateLayout();
                if (item.Key == "modeling")
                {
                    steps.SelectedValue = "die";
                    diagramTab.IsSelected = true;
                    steps.SelectedValue = item.Key;
                    Require(!schematic.HasDiagram && !diagramTab.IsEnabled && modelTab.IsSelected,
                        "建模与局部网格栏目不应提供示意图");
                    modelingCount++;
                    continue;
                }
                Require(modelTab.IsSelected && !diagramTab.IsSelected, "切换栏目时离开了三维模型：" + item.Key);
                Require(schematic.TemplateId == family.Id && schematic.StepKey == item.Key && schematic.DiagramKey.Length > 0,
                    "示意图没有跟随封装与栏目：" + family.Id + "/" + item.Key);
                var row = (ListBoxItem)steps.ItemContainerGenerator.ContainerFromItem(item);
                row.RaiseEvent(new MouseButtonEventArgs(Mouse.PrimaryDevice, Environment.TickCount, MouseButton.Left)
                    { RoutedEvent = UIElement.PreviewMouseUpEvent });
                Require(modelTab.IsSelected && !diagramTab.IsSelected, "再次点击当前栏目时离开了三维模型");
                diagramTab.IsSelected = true;
                steps.SelectedValue = item.Key == "summary" ? "die" : "summary";
                steps.SelectedValue = item.Key;
                window.UpdateLayout();
                Require(diagramTab.IsSelected && schematic.IsVisible && schematic.StepKey == item.Key,
                    "示意图页内切换栏目未保持视图或更新内容：" + item.Key);
                if (previews.Add(family.Id + "-" + schematic.DiagramKey))
                    Preview(workspace, item.Key, item.Label, family.Id + "-" + schematic.DiagramKey);
                count++;
            }
            if (steps.Items.Cast<WizardStep>().Any(s => s.Key == "metal_layers"))
            {
                steps.SelectedValue = "thermal_vias";
                string route = schematic.DiagramKey;
                steps.SelectedValue = "metal_layers";
                Require(schematic.DiagramKey == route, "通孔与金属层应共用基板细节图");
            }
        }
        workspace.Select("cbga_fc");
        steps.SelectedValue = "top_cover";
        foreach (string type in new[] { "bare_die", "encapsulant", "lid", "plate" })
        {
            workspace.Document.Values["cover.type"] = type;
            Preview(workspace, "top_cover", "顶部结构", "cbga_fc-cover-" + type);
        }
        steps.SelectedValue = "die";
        diagramTab.IsSelected = true;
        NewPackageChecks.Capture(window, "schematic-workspace.png");
        Console.WriteLine($"PASS {count} wizard schematics, {modelingCount} modeling sections without diagrams, shared diagrams and model tab switching");
    }

    static void Preview(Workspace workspace, string step, string label, string name)
    {
        var view = new PackageSchematic { Width = 700, Height = 580 };
        view.Update(workspace.Template, workspace.Document, step, label);
        view.Measure(new Size(700, 580));
        view.Arrange(new Rect(0, 0, 700, 580));
        view.UpdateLayout();
        var bitmap = new RenderTargetBitmap(700, 580, 96, 96, PixelFormats.Pbgra32);
        bitmap.Render(view);
        string directory = Environment.GetEnvironmentVariable("PACKSTUDIO_TEST_DIRECTORY") ??
            Path.GetFullPath("tmp/" + DateTime.Now.ToString("yyyy-MM-dd") + "-desktop-tests");
        Directory.CreateDirectory(directory);
        var encoder = new PngBitmapEncoder();
        encoder.Frames.Add(BitmapFrame.Create(bitmap));
        using var file = File.Create(Path.Combine(directory, name + ".png"));
        encoder.Save(file);
    }

    static void Require(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
    }
}
