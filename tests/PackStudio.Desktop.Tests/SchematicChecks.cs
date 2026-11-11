using System.IO;
using System.Reflection;
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
        DesLabelChecks.Run();
        var steps = (ListBox)window.FindName("StepList");
        var schematic = (PackageSchematic)window.FindName("Schematic");
        var modelTab = (LayoutDocument)window.FindName("ModelDocument");
        var diagramTab = (LayoutDocument)window.FindName("SchematicDocument");
        Require(ReferenceEquals(modelTab.Parent, diagramTab.Parent), "示意图与三维模型必须是同级标签页");
        int count = 0, modelingCount = 0;
        foreach (var family in workspace.Catalog.Families)
        {
            workspace.Select(family.Id);
            bool hasVias = steps.Items.Cast<WizardStep>().Any(s => s.Key == "thermal_vias");
            Require(hasVias == (family.Id is "chip_array" or "pbga_fc" or "pbga_wb" or "qfn"),
                "热通孔栏目与封装支持的参数不符：" + family.Id);
            Require(steps.Items.Cast<WizardStep>().Last().Key == "modeling", "建模栏目后出现了多余栏目：" + family.Id);
            object? sharedScene = null;
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
                if (family.Id == "chip_array" && item.Key is "thermal_vias" or "bond_wires")
                {
                    var labels = EditorLabels((StackPanel)window.FindName("FieldsPanel")).ToList();
                    string[] expected = item.Key == "thermal_vias" ? ["X 偏移 vxoff", "Y 偏移 vyoff", "孔径 dv"] :
                        ["线阵列长度 Lw", "线阵列宽度 Ww", "线径 dw"];
                    Require(expected.All(labels.Contains), "编辑区字段名称或符号与示意图不一致：" + item.Key);
                    NewPackageChecks.Capture(window, "chip_array-" + item.Key + "-editor.png");
                }
                if (item.Key is "central_solder_balls" or "solder_removal")
                {
                    bool central = item.Key == "central_solder_balls";
                    string option = central ? "包含中央焊球" : "主阵列中心去球";
                    string[] expected = central ? ["中央焊球行数 MEc", "中央焊球列数 MDc"] : ["外围满布行数 MEp", "外围满布列数 MDp"];
                    var fields = (StackPanel)window.FindName("FieldsPanel");
                    var checkbox = fields.Children.OfType<Grid>().SelectMany(row => row.Children.OfType<StackPanel>())
                        .SelectMany(panel => panel.Children.OfType<CheckBox>()).Single(box => Equals(box.Content, option));
                    bool initial = checkbox.IsChecked == true;
                    foreach (bool enabled in new[] { initial, !initial, initial })
                    {
                        checkbox.IsChecked = enabled;
                        window.UpdateLayout();
                        var labels = EditorLabels(fields).ToList();
                        string diagramText = LabelText(schematic);
                        string[] symbols = central ? ["MEc", "MDc"] : ["MEp", "MDp"];
                        Require(symbols.All(diagramText.Contains) && !diagramText.Contains("离板高度"),
                            $"焊球示意图标注与栏目不符：{family.Id}/{item.Key}");
                        if (family.Id == "cbga_fc")
                        {
                            var color = central ? Color.FromRgb(0xFF, 0xA0, 0) : Color.FromRgb(0x65, 0x3F, 0xFF);
                            Require(ColoredCircles(DrawingOf(schematic), color) == (central ? 4 : 44),
                                "中央焊球和去球图形应独立于启用开关");
                        }
                        Require(expected.All(label => labels.Contains(label) == enabled),
                            $"行列数未跟随「{option}」选项显示或隐藏：{family.Id}");

                    }
                }
                if (schematic.DiagramKey == "package")
                {
                    var scene = typeof(PackageSchematic).GetField("packageScene", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(schematic);
                    Require(scene != null && (sharedScene == null || ReferenceEquals(sharedScene, scene)),
                        "同一构图在栏目切换时重建了基础图形：" + family.Id + "/" + item.Key);
                    sharedScene = scene;
                }
                Preview(workspace, item.Key, item.Label, family.Id + "-" + item.Key);
                count++;
            }
            if (steps.Items.Cast<WizardStep>().Any(s => s.Key == "metal_layers"))
            {
                steps.SelectedValue = "thermal_vias";
                string route = schematic.DiagramKey;
                steps.SelectedValue = "metal_layers";
                Require(family.Id == "chip_array" ? schematic.DiagramKey != route : schematic.DiagramKey == route,
                    "通孔与金属层的图形路由不符合封装结构");
            }
            if (family.Id == "bare_die")
            {
                var sceneField = typeof(PackageSchematic).GetField("packageScene", BindingFlags.Instance | BindingFlags.NonPublic)!;
                steps.SelectedValue = "die";
                var originalScene = sceneField.GetValue(schematic);
                workspace.Document.Values["bumps.enabled"] = true;
                steps.SelectedValue = "summary";
                Require(ReferenceEquals(originalScene, sceneField.GetValue(schematic)), "裸芯片凸点开关改动了概要底图");
                steps.SelectedValue = "bumped_die";
                Require(LabelText(schematic).Contains("nballs"), "裸芯片凸点总数未随栏目显示");
                steps.SelectedValue = "die";
                var labels = LabelText(schematic);
                Require(labels.Contains("Wd") && !labels.Contains("nballs"), "裸芯片宽度或凸点标注未按栏目显示");
            }
        }
        workspace.Select("cbga_fc");
        foreach (string arrayType in new[] { "regular", "non_regular" })
        {
            workspace.Document.Values["bumps.array_type"] = arrayType;
            schematic.Update(workspace.Template, workspace.Document, "flip_chip_bumps", "凸点");
            Require(ColoredCircles(DrawingOf(schematic), Color.FromRgb(0x94, 0x77, 0xFF)) == 24 &&
                LabelText(schematic).Contains("MNC4"), "凸点图应始终显示满阵列和总数");
        }
        foreach (bool underfill in new[] { false, true })
        {
            workspace.Document.Values["bumps.underfill"] = underfill;
            schematic.Update(workspace.Template, workspace.Document, "flip_chip_bumps", "凸点");
            Require(HasUnderfill(DrawingOf(schematic)), "倒装凸点剖面应始终显示底填充");
        }
        foreach (bool staggered in new[] { false, true })
        {
            workspace.Document.Values["bga.staggered"] = staggered;
            schematic.Update(workspace.Template, workspace.Document, "solder_balls", "BGA 焊球");
            Require(ColoredCircles(DrawingOf(schematic), Color.FromRgb(0x65, 0x3F, 0xFF)) == (staggered ? 34 : 56),
                "交错主阵列未切换示意图");
        }

        steps.SelectedValue = "top_cover";
        foreach (string type in new[] { "bare_die", "encapsulant", "lid", "plate" })
        {
            workspace.Document.Values["cover.type"] = type;
            Preview(workspace, "top_cover", "顶部结构", "cbga_fc-cover-" + type);
        }
        workspace.Document.Values["cover.type"] = "lid";
        foreach (bool stiffened in new[] { false, true })
        {
            workspace.Document.Values["stiffener.enabled"] = stiffened;
            schematic.Update(workspace.Template, workspace.Document, "top_cover", "顶部结构");
            string labels = LabelText(schematic);
            Require(labels.Contains("Lsc") == stiffened && labels.Contains("tcb") != stiffened,
                "顶盖图应随加强环切换为相应结构");
        }
        Preview(workspace, "top_cover", "顶部结构", "cbga_fc-cover-stiffener");
        workspace.Document.Values["cover.type"] = "encapsulant";
        workspace.Document.Values["slug.enabled"] = false;
        schematic.Update(workspace.Template, workspace.Document, "top_cover", "顶部结构");
        var coverScene = typeof(PackageSchematic).GetField("packageScene", BindingFlags.Instance | BindingFlags.NonPublic)!;
        var coverWithoutSlug = coverScene.GetValue(schematic);
        workspace.Document.Values["slug.enabled"] = true;
        schematic.Update(workspace.Template, workspace.Document, "top_cover", "顶部结构");
        Require(ReferenceEquals(coverWithoutSlug, coverScene.GetValue(schematic)), "Slug 开关改动了顶部结构底图");
        Require(!LabelText(schematic).Contains("L_sl"), "顶部结构图混入了 Slug 尺寸");
        workspace.Document.Values["slug.enabled"] = false;
        workspace.Document.Values["cover.type"] = "lid";
        schematic.Update(workspace.Template, workspace.Document, "slug", "嵌入式散热块");
        Require(LabelText(schematic).Contains("L_sl") && LabelText(schematic).Contains("支脚粘接层"),
            "Slug 结构图应固定显示尺寸和粘接层");
        workspace.Select("pbga_fc");
        foreach (var (step, prefix, symbol) in new[] { ("upper_built_up", "upper", "dv_b1"), ("lower_built_up", "lower", "dv_b2") })
        {
            workspace.Document.Values[prefix + ".enabled"] = false;
            schematic.Update(workspace.Template, workspace.Document, step, "增层");
            string labels = LabelText(schematic);
            Require(labels.Contains(symbol) && labels.Contains("tzn") && !labels.Contains("基板厚度"),
                "增层图缺少微通孔和层表尺寸，或混入基板厚度");

        }
        workspace.Select("qfn");
        workspace.Document.Values["vias.enabled"] = false;
        schematic.Update(workspace.Template, workspace.Document, "thermal_vias", "热通孔");
        string viaLabels = LabelText(schematic);
        Require(viaLabels.Contains("通孔阵列局部俯视") &&
            !viaLabels.Contains("中央去除行数") && !viaLabels.Contains("中央去除列数"),
            "QFN 通孔局部图应保留，且不标注中央去除行列数");
        workspace.Select("cbga_fc");
        steps.SelectedValue = "die";
        diagramTab.IsSelected = true;
        NewPackageChecks.Capture(window, "schematic-workspace.png");
        Console.WriteLine($"PASS {count} wizard schematics, {modelingCount} modeling sections without diagrams, shared diagrams and model tab switching");
    }

    static DrawingGroup DrawingOf(PackageSchematic schematic) =>
        (DrawingGroup)typeof(PackageSchematic).GetField("drawing", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(schematic)!;

    static string LabelText(PackageSchematic schematic) => string.Join(" ", Glyphs(DrawingOf(schematic)));

    static int ColoredCircles(Drawing drawing, Color color) => drawing switch
    {
        DrawingGroup group => group.Children.Sum(child => ColoredCircles(child, color)),
        GeometryDrawing { Geometry: EllipseGeometry, Brush: SolidColorBrush brush } when brush.Color == color => 1,
        _ => 0
    };

    static bool HasUnderfill(Drawing drawing) => drawing switch
    {
        DrawingGroup group => group.Children.Any(HasUnderfill),
        GeometryDrawing { Geometry: RectangleGeometry rectangle, Brush: SolidColorBrush brush } =>
            brush.Color == Color.FromRgb(0x7A, 0x24, 0) && rectangle.Rect == new Rect(285, 215, 130, 15),
        _ => false
    };

    static IEnumerable<string> Glyphs(Drawing drawing) => drawing switch
    {
        DrawingGroup group => group.Children.SelectMany(Glyphs),
        GlyphRunDrawing glyph when glyph.GlyphRun.Characters is { } characters => [string.Concat(characters)],
        _ => []
    };

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

    static IEnumerable<string> EditorLabels(StackPanel fields) => fields.Children.OfType<Grid>()
        .Where(row => row.Visibility == Visibility.Visible && row.Children.Count > 0 && row.Children[0] is DockPanel)
        .Select(row => string.Join(" ", ((DockPanel)row.Children[0]).Children.OfType<TextBlock>()
            .Reverse().Select(label => label.Text.Trim())));
}
