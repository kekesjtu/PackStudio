using System.Windows.Media;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void ChipArrayVias()
    {
        PackageSection();
        DetailLink(ViaX(2), 245, 16, 350, 307, "通孔与焊球局部俯视");
        Rect(Board, 200, PlanTop, 300, PlanBottom - PlanTop);
        componentBrushes.Add(Solder);
        const double dx = 18, dy = -12;

        for (int row = 0; row < 5; row++)
            for (int col = 0; col < 9; col++)
            {
                double x = Centered(col, 9, 31), y = Centered(row, 5, BallRowPitch, PlanCenterY);
                dc.DrawEllipse(null, new Pen(Solder, 1.5), new(x, y), 8, 8);

                Ellipse(Metal, x + dx, y + dy, 5, 5);
                Ellipse(Brushes.White, x + dx, y + dy, 2.5, 2.5);
            }
        DimH(226, 226 + dx, FirstBallRow + dy, 355, "vias.offset_x");
        DimV(FirstBallRow + dy, FirstBallRow, 226 + dx, 160, "vias.offset_y", left: true);
        DimensionCallout("vias.diameter", 550, 345, 492, FirstBallRow + dy);
        DimensionCallout("vias.plating", 495, 589, 492, LastBallRow + dy);
        Axes(70, PlanBottom + 4);
        Legend((Solder, "焊球中心"), (Metal, "热通孔中心"), (Board, "基板"));
    }

    void ChipArrayMetal()
    {
        const double lengthFraction = 0.275, widthFraction = 0.25;
        const double planLeft = 412, planTop = 425, planSize = 152;
        double boardCenter = BgaBoardLeft + BgaBoardWidth / 2;
        double sectionOpeningLength = BgaBoardWidth * lengthFraction;
        var openingMaterial = Brush(Colors.LightSlateGray);

        PackageSection();
        Rect(openingMaterial, boardCenter - sectionOpeningLength / 2, SectionY,
            sectionOpeningLength, SectionMetalThickness, false);
        DetailLink(215, 245, 19, 200, 342, "金属层局部剖面");
        // Offset the leader within the central region so it clears the solder ball on the centerline.
        DetailLink(boardCenter - 18, SectionY + SectionMetalThickness / 2, 9,
            planLeft + planSize / 2, 342, "顶层开孔俯视");
        MetalStack(150, 425);

        double openingLength = planSize * lengthFraction, openingWidth = planSize * widthFraction;
        double openingLeft = planLeft + (planSize - openingLength) / 2;
        double openingTop = planTop + (planSize - openingWidth) / 2;
        double openingRight = openingLeft + openingLength;
        Rect(Metal, planLeft, planTop, planSize, planSize);
        Rect(openingMaterial, openingLeft, openingTop, openingLength, openingWidth);
        DimH(openingLeft, openingRight, openingTop, 400, "metal.hole_length");
        DimV(openingTop, openingTop + openingWidth, openingRight, 610, "metal.hole_width");
        Legend((Board, "介电层"), (Metal, "金属层"), (openingMaterial, "顶层中央区域"));
    }
}
