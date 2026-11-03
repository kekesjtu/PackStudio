using System.Windows.Media;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void SubstrateDetail()
    {
        Rect(Substrate, 160, 225, 380, 125);
        if (Qfn)
        {
            Rect(Metal, 260, 205, 180, 10);
            Rect(Solder, 260, 215, 180, 10);
            Callout("芯片承载焊盘", 240, 141, 290, 209);
            Callout("焊料 / 散热焊盘", 470, 160, 420, 220);
        }
        else
        {
            Rect(Die, 280, 172, 140, 26);
            if (Flip)
            {
                Rect(Attach, 280, 198, 140, 27);
                for (int i = 0; i < 4; i++) Ellipse(Bump, Centered(i, 4, 34), 211.5, 13.5, 13.5);
            }
            else
            {
                Rect(Attach, 280, 198, 140, 6);
                Rect(Metal, 265, 204, 170, 21);
                Wire(287, 172, 215, 225, 36); Wire(413, 172, 485, 225, 36);
            }
            Callout("芯片", 320, 125, 350, 182);
            Callout(Flip ? "底填充与凸点" : "承载台与粘接层", 480, 136, 408, 213);
        }
        if (family == "pbga_fc")
        {
            Rect(Brush("#00802C"), 160, 225, 380, 21);
            Rect(Brush("#00802C"), 160, 329, 380, 21);
            Text("上部增层", 52, 221, 12); Line(120, 234, 160, 234);
            Text("核心层", 65, 276, 12); Line(120, 287, 160, 287);
            Text("下部增层", 52, 332, 12); Line(120, 342, 160, 342);
        }
        for (int i = 0; i < 5; i++) Rect(Metal, 160, 227.5 + i * 29, 380, 4, false);
        for (int i = 0; i < 4; i++)
        {
            double x = Centered(i, 4, 48) - 6.5;
            Rect(Metal, x, 225, 13, 125);
            Rect(Brushes.White, x + 4, 225, 5, 125, false);
        }
        if (step == "upper_built_up") Outline(156, 221, 388, 29);
        if (step == "lower_built_up") Outline(156, 325, 388, 29);
        string thicknessKey = step == "upper_built_up" ? "upper.thickness" : step == "lower_built_up" ? "lower.thickness" : Qfn ? "vias.length" : "substrate.thickness";
        double y1 = step == "lower_built_up" ? 329 : 225;
        double y2 = step == "upper_built_up" ? 246 : 350;
        DimV(y1, y2, 540, 580, Dimension("厚度\n", thicknessKey));
        Rect(Substrate, 165, 455, 120, 112);
        Ellipse(Metal, 225, 511, 36, 36); Ellipse(Brushes.White, 225, 511, 23, 23);
        DimH(202, 248, 511, 428, Dimension("孔径", "vias.diameter", "dv"));
        Callout(Dimension("镀层厚度", "vias.plating", "tpl"), 110, 578, 194, 509);
        Rect(Substrate, 445, 455, 55, 112);
        const double layerPitch = 107.0 / 3;
        for (int i = 0; i < 4; i++) Rect(Metal, 445, 455 + i * layerPitch, 55, 5, false);
        DimV(455, 455 + 2 * layerPitch, 500, 537, "层深 zn");
        Callout("层厚 tzn", 571, 557, 487, 564.5);
    }

    void BallArray()
    {
        Rect(Board, 170, 171, 360, 24);
        for (int i = 0; i < 10; i++) Ellipse(Solder, Centered(i, 10, 36), 210, 15, 15);
        DimV(195, 225, 530, 571, Dimension("离板高度\n", "bga.height"));
        DimH(173, 203, 210, 259, Dimension("球径", "bga.diameter"));
        Rect(Board, 205, 350, 290, 225);
        bool central = step == "central_solder_balls";
        bool removal = step == "solder_removal";
        for (int row = 0; row < 7; row++)
            for (int col = 0; col < 9; col++)
            {
                bool middle = row is >= 2 and <= 4 && col is >= 3 and <= 5;
                double x = Centered(col, 9, 31), y = Centered(row, 7, 31, 462.5);
                bool omitted = middle && removal;
                Ellipse(omitted ? Brushes.White : middle && central ? Metal : Solder, x, y, 8, 8);
                if (omitted) { Line(x - 5, y - 5, x + 5, y + 5, Muted); Line(x + 5, y - 5, x - 5, y + 5, Muted); }
            }
        if (central || removal)
        {
            Outline(303.5, 416, 93, 93);
            Callout(central ? "中央焊球" : "去球区域", 430, 300, 396.5, 416);
        }
        DimH(226, 474, 575, 599, Dimension("X 方向列数", "bga.columns"));
        DimV(369.5, 555.5, 495, 535, Dimension("Y 方向行数\n", "bga.rows"));
        DimH(226, 257, 369.5, 331, Dimension("间距", "bga.pitch"));
        Axes(125, 560);
    }

    void Bumps()
    {
        Rect(Die, 205, 182, 290, 44);
        Rect(Attach, 205, 226, 290, 48);
        for (int i = 0; i < 5; i++) Ellipse(Bump, Centered(i, 5, 56), 250, 24, 24);
        if (!Bare) Rect(Board, 160, 274, 380, 25);
        Callout("芯片", 310, 133, 350, 195);
        Callout("底部填充材料", 510, 132, 490, 232);
        DimV(226, 274, 495, 555, Dimension("凸点高度\n", "bumps.height"));
        DimH(214, 262, 250, 318, Dimension("凸点直径", "bumps.diameter"));
        Rect(Die, 220, 420, 260, 140);
        for (int row = 0; row < 4; row++)
            for (int col = 0; col < 8; col++) Ellipse(Bump, Centered(col, 8, 32), Centered(row, 4, 34, 490), 8, 8);
        DimH(220, 480, 560, 592, Dimension("芯片长度", "die.length"));
        DimV(420, 560, 480, 535, Dimension("芯片宽度\n", "die.width"));
        Axes(140, 553);
    }

    void Leads()
    {
        Section(220);
        if (Qfn)
        {
            DimV(213, 225, 515, 562, Dimension("引脚厚度\n", "leads.thickness"));
            DimH(455, 515, 225, 281, Dimension("外露长度", "leads.length"));
        }
        else
        {
            DimV(219, 254, 550, 595, Dimension("引脚高度\n", "leads.height"));
            DimH(550, 580, 254, 292, Dimension("引脚足长", "leads.foot_length"));
        }
        Plan(frameDetail: true);
        if (!Qfn)
            for (int i = 0; i < 6; i++)
            {
                double outer = Centered(i, 6, 26, 470), inner = Centered(i, 6, 17, 470);
                Line(230, outer, 245, inner, Metal, 3);
                Line(470, outer, 455, inner, Metal, 3);
                if (!Sop)
                {
                    double pinX = Centered(i, 6, 48), fingerX = Centered(i, 6, 24);
                    Line(pinX, 390, fingerX, 400, Metal, 3);
                    Line(pinX, 550, fingerX, 540, Metal, 3);
                }
            }
        DimV(400, 426, 520, 558, Dimension("节距\n", Qfn ? "leads.pitch_y" : "leads.pitch"));
        DimV(452, 462, 520, 594, Dimension("线宽\n", "leads.width"));
        if (Qfn)
            DimH(200, 230, 435, 365, Dimension("外露长度", "leads.length"));
        else
        {
            Line(245, 470, 265, 470);
            Arrow(245, 470, 1, 0, length: 4); Arrow(265, 470, -1, 0, length: 4);
            Callout(Dimension("框架间隙", "leads.gap", "g1"), 170, 448, 255, 470, right: true);
        }
        DimH(200, 500, 550, 586, Dimension("封装长度", "package.length"));
        Axes(115, 552);
        Legend((Mold, "塑封"), (Metal, "引脚 / 框架"), (Die, "芯片"));
    }
}
