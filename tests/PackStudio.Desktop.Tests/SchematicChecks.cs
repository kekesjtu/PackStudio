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
        foreach (var family in PackageCatalog.Families)
        {
            workspace.Select(family.Id);
            bool hasVias = steps.Items.Cast<WizardStep>().Any(s => s.Key == "thermal_vias");
            Require(hasVias == (family.Id is "chip_array" or "pbga_fc" or "pbga_wb" or "qfn"),
                "热通孔栏目与封装支持的参数不符：" + family.Id);
            Require(steps.Items.Cast<WizardStep>().Last().Key == "modeling", "建模栏目后出现了多余栏目：" + family.Id);
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
                    Require(!schematic.HasDiagram && diagramTab.IsEnabled && modelTab.IsSelected,
                        "选择建模与局部网格时未保留三维模型标签页");
                    steps.SelectedValue = "die";
                    diagramTab.IsSelected = true;
                    steps.SelectedValue = item.Key;
                    Require(!schematic.HasDiagram && diagramTab.IsEnabled && diagramTab.IsSelected,
                        "选择建模与局部网格时应保留空白示意图标签页");
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
                Preview(workspace, item.Key, item.Label, family.Id + "-" + item.Key);
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
        workspace.Document.Values["cover.type"] = "lid";
        workspace.Document.Values["stiffener.enabled"] = true;
        Preview(workspace, "top_cover", "顶部结构", "cbga_fc-cover-stiffener");
        foreach (string family in new[] { "cbga_fc", "pbga_wb" })
        {
            workspace.Select(family);
            workspace.Document.Values["slug.adhesive_enabled"] = true;
            Preview(workspace, "slug", "嵌入式散热块", family + "-slug-adhesive");
        }
        workspace.Select("bare_die");
        workspace.Document.Values["bumps.enabled"] = true;
        Preview(workspace, "die", "芯片", "bare_die-die-bumped");
        workspace.Select("cbga_fc");
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
