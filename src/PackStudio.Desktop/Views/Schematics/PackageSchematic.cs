using System.Windows;
using System.Windows.Media;
using PackStudio.Core;

namespace PackStudio.Desktop;

/// <summary>Resolution independent parameter illustrations, separate from generated geometry.</summary>
public sealed class PackageSchematic : FrameworkElement
{
    DrawingGroup? drawing;
    public string TemplateId { get; private set; } = "";
    public string StepKey { get; private set; } = "";
    public string DiagramKey { get; private set; } = "";
    public bool HasDiagram => DiagramKey.Length > 0;

    public void Update(Template template, ProjectDocument document, string step, string label)
    {
        TemplateId = document.TemplateId;
        StepKey = step;
        DiagramKey = Route(step);
        ToolTip = HasDiagram ? $"{template.Info.Name} · {label}" : null;
        drawing = HasDiagram ? new SchematicDrawing(template, document, step).Create(DiagramKey) : null;
        InvalidateVisual();
    }

    static string Route(string step) => step switch
    {
        "thermal_vias" or "metal_layers" or "upper_built_up" or "lower_built_up" => "substrate",
        "solder_balls" or "central_solder_balls" or "solder_removal" => "balls",
        "flip_chip_bumps" or "bumped_die" => "bumps",
        "leadframe" or "lead_solder_interconnect" => "leads",
        "bond_wires" => "wires",
        "top_cover" => "cover",
        "slug" => "slug",
        "backside_spreader" => "spreader",
        "modeling" => "",
        "summary" or "overall_package" or "package_substrate" or "die" or "encapsulant" or
            "die_flag_solder_mask" or "die_flag_tie_bars" or "dap" or "thermal_land" or "thermal_land_solder" => "package",
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
