using System.Windows;
using System.Windows.Media;
using PackStudio.Core;
using Newtonsoft.Json.Linq;

namespace PackStudio.Desktop;

/// <summary>Resolution independent parameter illustrations, separate from generated geometry.</summary>
public sealed class PackageSchematic : FrameworkElement
{
    DrawingGroup? drawing;
    DrawingGroup? packageScene;
    JArray? sceneValues;
    string sceneTemplate = "";
    static readonly string[] SceneKeys = ["die.flipped", "bumps.enabled", "bumps.underfill", "cover.type",
        "stiffener.enabled", "slug.enabled", "slug.adhesive_enabled", "spreader.enabled", "thermal_land.enabled",
        "vias.enabled", "vias.filled", "substrate.layers", "metal.layers"];
    public string TemplateId { get; private set; } = "";
    public string StepKey { get; private set; } = "";
    public string DiagramKey { get; private set; } = "";
    public bool HasDiagram => DiagramKey.Length > 0;

    public void Update(Template template, ProjectDocument document, string step, string label)
    {
        TemplateId = document.TemplateId;
        StepKey = step;
        DiagramKey = Route(document.TemplateId, step);
        ToolTip = HasDiagram ? $"{template.Info.Name} · {label}" : null;
        var renderer = new SchematicDrawing(template, document, step);
        var configuration = new JArray(SceneKeys.Select(key => document.Values[key]?.DeepClone() ?? JValue.CreateNull()));
        if (DiagramKey == "package" && (packageScene == null || sceneTemplate != TemplateId || !JToken.DeepEquals(sceneValues, configuration)))
        {
            packageScene = renderer.CreatePackageScene();
            sceneValues = configuration;
            sceneTemplate = TemplateId;
        }
        drawing = HasDiagram ? renderer.Create(DiagramKey, packageScene) : null;
        InvalidateVisual();
    }

    static string Route(string template, string step) => step switch
    {
        "thermal_vias" when template == "chip_array" => "chip_vias",
        "metal_layers" when template == "chip_array" => "chip_metal",
        "thermal_vias" or "metal_layers" or "upper_built_up" or "lower_built_up" => "substrate",
        "solder_balls" or "central_solder_balls" or "solder_removal" => "balls",
        "modeling" => "",
        "summary" or "overall_package" or "package_substrate" or "die" or "encapsulant" or
            "die_flag_solder_mask" or "die_flag_tie_bars" or "dap" or "thermal_land" or "thermal_land_solder" or
            "flip_chip_bumps" or "bumped_die" or "leadframe" or "lead_solder_interconnect" or "bond_wires" or
            "top_cover" or "slug" or "backside_spreader" => "package",
        _ => throw new ArgumentOutOfRangeException(nameof(step), step, "栏目没有对应的示意图。")
    };

    protected override void OnRender(DrawingContext dc)
    {
        base.OnRender(dc);
        if (drawing == null || ActualWidth <= 0 || ActualHeight <= 0) return;
        double scale = Math.Min(ActualWidth / SchematicDrawing.Width, ActualHeight / SchematicDrawing.Height);
        dc.PushTransform(new TranslateTransform((ActualWidth - SchematicDrawing.Width * scale) / 2,
            (ActualHeight - SchematicDrawing.Height * scale) / 2));
        dc.PushTransform(new ScaleTransform(scale, scale));
        dc.DrawDrawing(drawing);
        dc.Pop();
        dc.Pop();
    }
}
