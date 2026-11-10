using System.Windows;
using System.Windows.Media;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    const double BallRowPitch = 38;
    const double FirstBallRow = PlanCenterY - 2 * BallRowPitch, LastBallRow = PlanCenterY + 2 * BallRowPitch;

    void BallArray()
    {
        bool removed = Checked("bga.solder_removal_enabled"), central = Checked("bga.center_solder_enabled");
        bool staggered = Checked("bga.staggered");
        PackageSection(removeCentralBalls: removed);
        Rect(Board, 200, PlanTop, 300, PlanBottom - PlanTop);
        for (int row = 0; row < 5; row++)
            for (int col = 0; col < 9; col++)
            {
                bool middle = row is >= 1 and <= 3 && col is >= 3 and <= 5;
                if ((!removed || !middle) && (!staggered || (row + col) % 2 == 0))
                    Ellipse(Solder, Centered(col, 9, 31), Centered(row, 5, BallRowPitch, PlanCenterY), 8, 8);
            }
        if (central)
        {
            double firstRow = PlanCenterY - BallRowPitch / 2, lastRow = PlanCenterY + BallRowPitch / 2;
            bool centerStaggered = Checked("bga.center_staggered");
            for (int row = 0; row < 2; row++)
                for (int col = 0; col < 2; col++)
                    if (!centerStaggered || row == col)
                        Ellipse(Metal, Centered(col, 2, 31), Centered(row, 2, BallRowPitch, PlanCenterY), 8, 8);
            DimH(334.5, 365.5, firstRow, 340, "bga.center_solder_columns");
            DimV(firstRow, lastRow, 365.5, 550, "bga.center_solder_rows");
        }
        if (removed)
        {
            DashedRect(303.5, PlanCenterY - 1.5 * BallRowPitch, 93, 3 * BallRowPitch);
            PopulatedBandDimensions();
        }
        DimV(260, 282, 550, 580, "bga.height");
        DimH(155, 177, 271, 310, "bga.diameter");
        DimH(226, 474, PlanBottom, PlanLengthDimensionY, "bga.columns");
        DimV(FirstBallRow, LastBallRow, 500, 550, "bga.rows");
        DimH(226, 257, FirstBallRow, 355, "bga.pitch");
        Axes(70, PlanBottom + 4);
        if (central) Legend((Board, "基板"), (Solder, "BGA 焊球"), (Metal, "中央焊球"));
        else Legend((Board, "基板"), (Solder, "BGA 焊球"));
    }

    void PopulatedBandDimensions()
    {
        foreach (var (left, right) in new[] { (210.5, 303.5), (396.5, 489.5) })
        {
            Line(left, PlanTop, left, 345); Line(right, PlanTop, right, 345);
            Line(left, 350, right, 350); Arrow(left, 350, 1, 0); Arrow(right, 350, -1, 0);
            Line((left + right) / 2, 350, (left + right) / 2, 330);
        }
        Line(257, 330, 443, 330);
        DimensionText("bga.populated_columns", 350, 305, TextAlignment.Center);
        double halfPitch = BallRowPitch / 2;
        foreach (double y in new[] { FirstBallRow, LastBallRow })
        {
            double top = y - halfPitch, bottom = y + halfPitch;
            Line(200, top, 150, top); Line(200, bottom, 150, bottom);
            Line(155, top, 155, bottom); Arrow(155, top, 0, 1); Arrow(155, bottom, 0, -1);
            Line(155, y, 115, y);
        }
        Line(115, FirstBallRow, 115, LastBallRow);
        DimensionText("bga.populated_rows", 105, 453, TextAlignment.Right, "\n");
    }

    void SubstrateDetail()
    {
        PackageSection();
        switch (step)
        {
            case "thermal_vias" when Checked("vias.enabled"):
                ViaDetails();
                break;
            case "metal_layers":
                MetalStack("metal.layers", 285, 403);
                Legend((Board, "介电层"), (Metal, "金属层"));
                break;
            case "upper_built_up" when Checked("upper.enabled"):
                BuiltUp("upper", 230);
                break;
            case "lower_built_up" when Checked("lower.enabled"):
                BuiltUp("lower", 254);
                break;
            default:
                Plan();
                Axes(70, PlanBottom + 4);
                PackageLegend();
                break;
        }
    }

    void ViaDetails()
    {
        bool remove = Checked("vias.removal_enabled");
        Rect(Board, 165, 390, 228, 164);
        for (int row = 0; row < 5; row++)
            for (int col = 0; col < 7; col++)
                if (!remove || row is 0 or 4 || col is < 2 or > 4)
                {
                    double x = Centered(col, 7, 30, 279), y = Centered(row, 5, 28, 472);
                    Ellipse(Metal, x, y, 6, 6);
                    Ellipse(Brushes.White, x, y, 3, 3);
                }
        DimH(189, 219, 416, 375, "vias.pitch");
        BracketH(189, 369, 566, "vias.columns");
        BracketV(148, 416, 528, "vias.rows", 393);
        if (remove)
        {
            DashedRect(234, 430, 90, 84);
            BracketH(234, 324, 524, "vias.removal_columns");
            BracketV(400, 430, 514, "vias.removal_rows", 370);
        }
        ViaInset(514, 454, "vias", filled: false);
        if (Qfn)
        {
            Rect(Metal, 521, 550, 22, 54);
            Rect(Brushes.White, 526, 550, 12, 54);
            DimV(550, 604, 543, 580, "vias.length");
        }
        Axes(70, PlanBottom + 4);
        Legend((Board, "基材"), (Metal, "通孔镀层"));
    }

    void BuiltUp(string prefix, double top)
    {
        Rect(Board, 150, top, 400, 6);
        DimV(top, top + 6, 550, 590, prefix + ".thickness");
        MetalStack(prefix + ".layers", 192, 403);
        ViaInset(499, 462, prefix, Checked(prefix + ".filled"));
        DimensionText(prefix + ".count", 499, 581, TextAlignment.Center);
        Legend((Board, "介电层"), (Metal, "金属层 / 镀层"));
    }

    void ViaInset(double x, double y, string prefix, bool filled)
    {
        Rect(Board, x - 48, y - 45, 96, 90);
        Ellipse(Metal, x, y, 27, 27);
        Ellipse(filled ? Attach : Brushes.White, x, y, 17, 17);
        DimH(x - 27, x + 27, y, y - 66, prefix + ".diameter");
        DimH(x + 17, x + 27, y, y + 65, prefix + ".plating");
    }

    void MetalStack(string key, double x, double y)
    {
        if (Field(key) == null) return;
        Rect(Board, x, y, 100, 142);
        int layers = LayerCount(key);
        double pitch = 136.0 / (layers - 1);
        for (int i = 0; i < layers; i++) Rect(Metal, x, y + i * pitch, 100, 6, false);
        DrawDimV(y, y + pitch, x, x - 30, "层深\nzn", left: true);
        Callout("层厚  tzn", x + 110, y + 62, x + 98, y + 3);
    }

    void DashedRect(double x, double y, double width, double height) =>
        dc.DrawRectangle(null, new Pen(Ink, 1) { DashStyle = DashStyles.Dash }, new(x, y, width, height));
}
