using System.Windows.Media;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void BallArray()
    {
        PackageSection();
        Rect(Board, 200, 390, 300, 160);
        bool removed = Enabled("bga.solder_removal_enabled"), central = Enabled("bga.center_solder_enabled");
        for (int row = 0; row < 5; row++)
            for (int col = 0; col < 9; col++)
            {
                bool middle = row is >= 1 and <= 3 && col is >= 3 and <= 5;
                double x = Centered(col, 9, 31), y = Centered(row, 5, 31, 470);
                if (removed && middle && !central)
                    dc.DrawEllipse(null, new Pen(Muted, 1) { DashStyle = DashStyles.Dash }, new(x, y), 8, 8);
                else Ellipse(middle && central ? Metal : Solder, x, y, 8, 8);
            }
        if (step is "central_solder_balls" or "solder_removal")
        {
            Outline(303.5, 423.5, 93, 93);
            Callout(step == "central_solder_balls" ? "中央焊球" : "去球区域", 430, 310, 396.5, 423.5);
        }
        DimV(260, 282, 550, 580, Dimension("离板高度\n", "bga.height"));
        DimH(155, 177, 271, 310, Dimension("球径", "bga.diameter"));
        DimH(226, 474, 550, 579, Dimension("X 方向列数", "bga.columns"));
        DimV(408, 532, 500, 550, Dimension("Y 方向行数\n", "bga.rows"));
        DimH(226, 257, 408, 365, Dimension("间距", "bga.pitch"));
        Axes(70, 554);
        Legend((Board, "基板"), (Solder, "BGA 焊球"), (Metal, "中央焊球"));
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
