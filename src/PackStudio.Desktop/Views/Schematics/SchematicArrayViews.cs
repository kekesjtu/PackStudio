using System.Windows.Media;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void BallArray()
    {
        bool removed = step == "solder_removal", central = step == "central_solder_balls";
        PackageSection(removeCentralBalls: removed);
        Rect(Board, 200, 390, 300, 160);
        for (int row = 0; row < 5; row++)
            for (int col = 0; col < 9; col++)
            {
                bool middle = row is >= 1 and <= 3 && col is >= 3 and <= 5;
                double x = Centered(col, 9, 31), y = Centered(row, 5, 31, 470);
                if (!removed || !middle) Ellipse(Solder, x, y, 8, 8);
            }
        if (central)
        {
            for (int row = 0; row < 2; row++)
                for (int col = 0; col < 2; col++)
                    Ellipse(Metal, Centered(col, 2, 31), Centered(row, 2, 31, 470), 8, 8);
            Callout("中央焊球", 170, 430, 334.5, 454.5, right: true);
            DimH(334.5, 365.5, 454.5, 340, Dimension("中央焊球列数", "bga.center_solder_columns"));
            DimV(454.5, 485.5, 365.5, 550, Dimension("中央焊球行数\n", "bga.center_solder_rows"));
        }
        if (removed)
        {
            Outline(294, 260, 112, 24);
            Outline(303.5, 423.5, 93, 93);
            PopulatedBandDimensions();
        }
        DimV(260, 282, 550, 580, Dimension("离板高度\n", "bga.height"));
        DimH(155, 177, 271, 310, Dimension("球径", "bga.diameter"));
        DimH(226, 474, 550, 579, Dimension("X 方向列数", "bga.columns"));
        DimV(408, 532, central ? 200 : 500, central ? 155 : 550,
            Dimension("Y 方向行数\n", "bga.rows"), central);
        if (!central && !removed) DimH(226, 257, 408, 365, Dimension("间距", "bga.pitch"));
        Axes(70, 554);
        Legend((Board, "基板"), (Solder, "BGA 焊球"), (Metal, "中央焊球"));
    }

    void PopulatedBandDimensions()
    {
        foreach (var (left, right) in new[] { (210.5, 303.5), (396.5, 489.5) })
        {
            Line(left, 390, left, 345); Line(right, 390, right, 345);
            Line(left, 350, right, 350); Arrow(left, 350, 1, 0); Arrow(right, 350, -1, 0);
            Line((left + right) / 2, 350, (left + right) / 2, 330);
        }
        Line(257, 330, 443, 330);
        Text(Dimension("外围满布列数", "bga.populated_columns"), 350, 305, align: System.Windows.TextAlignment.Center);
        foreach (var (top, bottom) in new[] { (392.5, 423.5), (516.5, 547.5) })
        {
            Line(200, top, 150, top); Line(200, bottom, 150, bottom);
            Line(155, top, 155, bottom); Arrow(155, top, 0, 1); Arrow(155, bottom, 0, -1);
            Line(155, (top + bottom) / 2, 115, (top + bottom) / 2);
        }
        Line(115, 408, 115, 532);
        Text(Dimension("外围满布行数\n", "bga.populated_rows"), 105, 453, align: System.Windows.TextAlignment.Right);
    }

    void SubstrateDetail()
    {
        PackageSection();
        Rect(Substrate, 165, 425, 120, 112);
        Ellipse(Metal, 225, 481, 36, 36); Ellipse(Brushes.White, 225, 481, 23, 23);
        DimH(202, 248, 481, 395, Dimension("孔径", "vias.diameter", "dv"));
        Callout(Dimension("镀层厚度", "vias.plating", "tpl"), 110, 558, 194, 479);
        Rect(Substrate, 445, 425, 55, 112);
        double pitch = 107.0 / (LayerCount - 1);
        for (int i = 0; i < LayerCount; i++) Rect(Metal, 445, 425 + i * pitch, 55, 5, false);
        DimV(425, 425 + pitch, 500, 537, "层深 zn");
        Callout("层厚 tzn", 571, 527, 487, 534.5);
        if (step is "upper_built_up" or "lower_built_up")
        {
            bool upper = step == "upper_built_up";
            double y = upper ? 230 : 254;
            Outline(146, y - 4, 408, 14);
            DimV(y, y + 6, 550, 590, Dimension("增层厚度\n", upper ? "upper.thickness" : "lower.thickness"));
        }
        else DimV(230, 260, 550, 590, Dimension("基板厚度\n", "substrate.thickness"));
        Legend((Substrate, "介电层"), (Metal, "金属层 / 镀层"));
    }
}
