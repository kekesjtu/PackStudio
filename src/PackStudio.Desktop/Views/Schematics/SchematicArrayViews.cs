using System.Windows;
using System.Windows.Media;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void SubstrateDetail()
    {
        Rect(Substrate, 160, 225, 380, 125);
        for (int i = 0; i < 5; i++) Rect(Metal, 160, 228 + i * 29, 380, 4, false);
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
                for (int i = 0; i < 6; i++) Ellipse(Solder, 292 + i * 23, 212, 8, 10);
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
            Rect(Brush("#438662"), 160, 225, 380, 21);
            Rect(Brush("#438662"), 160, 329, 380, 21);
            Text("上部增层", 52, 221, 12); Line(120, 234, 160, 234, Muted);
            Text("核心层", 65, 276, 12); Line(120, 287, 160, 287, Muted);
            Text("下部增层", 52, 332, 12); Line(120, 342, 160, 342, Muted);
        }
        for (int i = 0; i < 4; i++)
        {
            double x = 273 + i * 48;
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
        for (int i = 0; i < 4; i++) Rect(Metal, 445, 459 + i * 31, 55, 5, false);
        DimV(455, 521, 500, 537, "层深 zn");
        Callout("层厚 tzn", 571, 557, 487, 554);
        Text("层表：深度、厚度与铜覆盖率", 350, 624, 12, Muted, TextAlignment.Center);
    }

    void BallArray()
    {
        Rect(family == "cbga_fc" ? Cover : Substrate, 170, 171, 360, 24);
        for (int i = 0; i < 10; i++) Ellipse(Solder, 188 + i * 36, 214, 13, 15);
        DimV(195, 229, 530, 571, Dimension("离板高度\n", "bga.height"));
        DimH(175, 201, 214, 259, Dimension("球径", "bga.diameter"));
        DimH(224, 260, 214, 145, Dimension("球间距", "bga.pitch"));
        Rect(Brush("#F2F7F5"), 205, 350, 290, 225);
        bool central = step == "central_solder_balls";
        bool removal = step == "solder_removal";
        for (int row = 0; row < 7; row++)
            for (int col = 0; col < 9; col++)
            {
                bool middle = row is >= 2 and <= 4 && col is >= 3 and <= 5;
                double x = 225 + col * 31, y = 369 + row * 31;
                bool omitted = middle && removal;
                Ellipse(omitted ? Brushes.White : middle && central ? Metal : Solder, x, y, 8, 8);
                if (omitted) { Line(x - 5, y - 5, x + 5, y + 5, Muted); Line(x + 5, y - 5, x - 5, y + 5, Muted); }
            }
        if (central || removal)
        {
            Outline(306, 414, 93, 93);
            Callout(central ? "独立中央焊球阵列" : "中心去球 / 自定义去球", 430, 317, 393, 419);
        }
        DimH(225, 473, 575, 599, Dimension("X 方向列数", "bga.columns"));
        DimV(369, 555, 495, 535, Dimension("Y 方向行数\n", "bga.rows"));
        DimH(225, 256, 369, 331, Dimension("间距", "bga.pitch"));
        Axes(125, 560);
        Text(central ? "中央阵列可单独启用，并设置行列数与交错排列。" : removal ?
            "虚线区域表示去球范围；也可逐格选择省略的焊球。" : "规则阵列示意；行列数、交错排列与球图由左侧参数设置。", 350, 634, 12, Muted, TextAlignment.Center);
    }

    void Bumps()
    {
        Rect(Die, 205, 182, 290, 44);
        Rect(Attach, 205, 226, 290, 48);
        for (int i = 0; i < 8; i++) Ellipse(Solder, 223 + i * 36, 250, 12, 20);
        if (!Bare) Rect(Substrate, 160, 274, 380, 25);
        Callout("芯片", 310, 133, 350, 195);
        Callout("底部填充材料", 510, 132, 490, 232);
        DimV(226, 274, 495, 555, Dimension("凸点高度\n", "bumps.height"));
        DimH(211, 235, 250, 318, Dimension("凸点直径", "bumps.diameter"));
        Rect(Die, 220, 420, 260, 140);
        for (int row = 0; row < 4; row++)
            for (int col = 0; col < 8; col++) Ellipse(Solder, 238 + col * 32, 438 + row * 34, 8, 8);
        DimH(220, 480, 560, 592, Dimension("芯片长度", "die.length"));
        DimV(420, 560, 480, 535, Dimension("芯片宽度\n", "die.width"));
        Axes(140, 553);
        Text(Bare ? "凸点数量与直径用于等效建模；可选凸点与底填充。" :
            "规则阵列指定行列数；非规则阵列以凸点总数进行等效。", 350, 632, 12, Muted, TextAlignment.Center);
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
        Plan();
        if (!Qfn)
            for (int i = 0; i < 6; i++)
            {
                Line(230, 405 + i * 26, 265, 425 + i * 17, Metal, 3);
                Line(470, 405 + i * 26, 435, 425 + i * 17, Metal, 3);
            }
        DimV(400, 426, 520, 558, Dimension("节距\n", Qfn ? "leads.pitch_y" : "leads.pitch"));
        DimV(452, 462, 520, 594, Dimension("线宽\n", "leads.width"));
        DimH(Qfn ? 200 : 230, Qfn ? 230 : 265, 435, 365,
            Qfn ? Dimension("外露长度", "leads.length") : Dimension("框架间隙", "leads.gap", "g1"));
        DimH(200, 500, 550, 586, Dimension("封装长度", "package.length"));
        Axes(115, 552);
        Legend((Mold, "塑封"), (Metal, "引脚 / 框架"), (Die, "芯片"));
    }
}
