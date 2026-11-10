using System.Windows;
using System.Windows.Media;
using PackStudio.Core;


namespace PackStudio.Desktop;

/// <summary>Resolution independent parameter illustrations, separate from generated geometry.</summary>
public sealed class PackageSchematic : FrameworkElement
{
    DrawingGroup? drawing;
    DrawingGroup? packageScene;
    string sceneCoverType = "";
    string sceneTemplate = "";
    public string TemplateId { get; private set; } = "";
    public string StepKey { get; private set; } = "";
    public string DiagramKey { get; private set; } = "";
    public bool HasDiagram => DiagramKey.Length > 0;

    public void Update(PackageDefinition template, ProjectDocument document, string step, string label)
    {
        TemplateId = document.TemplateId;
        StepKey = step;
        DiagramKey = template.Steps.Single(s => s["key"].Text() == step)["diagram"].Text();
        ToolTip = HasDiagram ? $"{template.Info.Name} · {label}" : null;
        var renderer = new SchematicDrawing(template, document, step);
        DrawingGroup? scene = null;
        if (DiagramKey == "package")
        {
            if (renderer.HasLocalPackageScene)
                scene = renderer.CreatePackageScene();
            else
            {
                if (packageScene == null || sceneTemplate != TemplateId || sceneCoverType != renderer.CoverType)
                {
                    packageScene = renderer.CreatePackageScene();
                    sceneCoverType = renderer.CoverType;
                    sceneTemplate = TemplateId;
                }
                scene = packageScene;
            }
        }
        drawing = HasDiagram ? renderer.Create(DiagramKey, scene) : null;
        InvalidateVisual();
    }

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
