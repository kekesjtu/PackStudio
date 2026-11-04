using System.Windows.Media;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void ChipArrayVias()
    {
        PackageSection();
        Callout("热通孔", 485, 150, Centered(4, 11, 36.8) + 18, 245);
        Rect(Board, 200, 390, 300, 160);
        const double dx = 18, dy = -12;
        for (int row = 0; row < 5; row++)
            for (int col = 0; col < 9; col++)
            {
                double x = Centered(col, 9, 31), y = Centered(row, 5, 31, 470);
                dc.DrawEllipse(null, new Pen(Solder, 1.5), new(x, y), 8, 8);
                Ellipse(Metal, x + dx, y + dy, 5, 5);
                if (!Enabled("vias.filled")) Ellipse(Brushes.White, x + dx, y + dy, 2.5, 2.5);
            }
        DimH(226, 226 + dx, 396, 355, Dimension("X 偏移", "vias.offset_x"));
        DimV(408 + dy, 408, 226 + dx, 160, Dimension("Y 偏移\n", "vias.offset_y"), true);
        Callout(Dimension("孔径", "vias.diameter"), 550, 345, 492, 396);
        if (!Enabled("vias.filled")) Callout(Dimension("镀层厚度", "vias.plating"), 495, 578, 492, 520);
        Axes(70, 554);
        Legend((Solder, "焊球中心"), (Metal, "热通孔中心"), (Board, "基板"));
    }

    void ChipArrayMetal()
    {
        PackageSection();
        Callout("顶层铜", 485, 150, 505, 233.5);
        Callout("底层铜", 70, 295, 150, 255.5);
        Rect(Board, 190, 425, 90, 125);
        double layerPitch = 120.0 / (LayerCount - 1), layerY = 425 + layerPitch;
        for (int i = 0; i < LayerCount; i++) Rect(Metal, 190, 425 + i * layerPitch, 90, 5);
        DimV(425, layerY, 190, 155, "层深\nzn", true);
        DimV(layerY, layerY + 5, 280, 315, "层厚\ntzn");
        Rect(Metal, 410, 425, 150, 125);
        Rect(Board, 450, 455, 70, 65);
        DimH(450, 520, 455, 395, Dimension("顶层开孔长度", "metal.hole_length"));
        DimV(455, 520, 560, 590, Dimension("孔宽\n", "metal.hole_width"));
        DimV(230, 260, 150, 115, Dimension("基板厚度\n", "substrate.thickness"), true);
        Legend((Board, "介电层"), (Metal, "金属层"));
    }
}
