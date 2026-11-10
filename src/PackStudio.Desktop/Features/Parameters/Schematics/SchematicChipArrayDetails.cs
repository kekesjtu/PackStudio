using System.Windows.Media;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void ChipArrayVias()
    {
        PackageSection();
        bool enabled = Checked("vias.enabled");
        if (enabled) Callout("热通孔", 485, 150, Centered(4, 11, 36.8) + 18, 245);
        Rect(Board, 200, PlanTop, 300, PlanBottom - PlanTop);
        const double dx = 18, dy = -12;
        bool filled = Checked("vias.filled");
        for (int row = 0; row < 5; row++)
            for (int col = 0; col < 9; col++)
            {
                double x = Centered(col, 9, 31), y = Centered(row, 5, BallRowPitch, PlanCenterY);
                dc.DrawEllipse(null, new Pen(Solder, 1.5), new(x, y), 8, 8);
                if (!enabled) continue;
                Ellipse(Metal, x + dx, y + dy, 5, 5);
                if (!filled) Ellipse(Brushes.White, x + dx, y + dy, 2.5, 2.5);
            }
        DimH(226, 226 + dx, FirstBallRow + dy, 355, "vias.offset_x");
        DimV(FirstBallRow + dy, FirstBallRow, 226 + dx, 160, "vias.offset_y", left: true);
        DimensionCallout("vias.diameter", 550, 345, 492, FirstBallRow + dy);
        DimensionCallout("vias.plating", 495, 589, 492, LastBallRow + dy);
        Axes(70, PlanBottom + 4);
        if (enabled) Legend((Solder, "焊球中心"), (Metal, "热通孔中心"), (Board, "基板"));
        else Legend((Solder, "焊球中心"), (Board, "基板"));
    }

    void ChipArrayMetal()
    {
        PackageSection();
        Callout("顶层铜", 485, 150, 505, 233.5);
        Callout("底层铜", 70, 295, 150, 255.5);
        MetalStack("metal.layers", 165, 425);
        Rect(Metal, 410, 425, 150, 125);
        Rect(Board, 450, 455, 70, 65);
        DimH(450, 520, 455, 395, "metal.hole_length");
        DimV(455, 520, 520, 590, "metal.hole_width");
        Legend((Board, "介电层"), (Metal, "金属层"));
    }
}
