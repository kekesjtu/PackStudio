using System.Windows;
using System.Windows.Media;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void Section(double y, bool drawMold = true, double wireEnd = 226, bool removeCentralBalls = false)
    {
        if (Bare)
        {
            Rect(Die, 240, y - 20, 220, 34);
            double activeY = y + (Enabled("die.flipped") || Enabled("bumps.enabled") ? 14 : -20);
            Line(240, activeY, 460, activeY, Accent, 3);
            if (Enabled("bumps.enabled"))
            {
                Rect(Attach, 240, y + 14, 220, 23);
                for (int i = 0; i < 8; i++) Ellipse(Bump, Centered(i, 8, 27), y + 25.5, 11.5, 11.5);
            }
            return;
        }
        if (Bga)
        {
            if (!Flip && drawMold) Rect(Mold, ChipArray ? 150 : 195, y - 67, ChipArray ? 400 : 310, 67);
            Rect(Board, 150, y, 400, 30);
            if (!CeramicBoard)
            {
                for (int layer = 0; layer < LayerCount; layer++)
                    Rect(Metal, 150, y + 2 + layer * 22.0 / (LayerCount - 1), 400, 3, false);
            }
            if (Enabled("vias.enabled"))
                for (int i = 0; i < 4; i++)
                {
                    double x = ChipArray ? Centered(2 + i * 2, 11, 36.8) + 18 : Centered(i, 4, 32);
                    Rect(Metal, x - 3, y + 5, 6, 19);
                    if (!Enabled("vias.filled")) Rect(Brushes.White, x - 1, y + 5, 2, 19, false);
                }
            for (int i = 0; i < 11; i++)
                if (!removeCentralBalls || i is < 4 or > 6)
                    Ellipse(Solder, Centered(i, 11, 36.8), y + 41, 11, 11);
            if (Flip)
            {
                Rect(Die, 285, FlipDieTop(y), 130, 23);
                if (Enabled("bumps.underfill")) Rect(Attach, 285, y - 2 * FlipBumpRadius, 130, 2 * FlipBumpRadius);
                for (int i = 0; i < 6; i++) Ellipse(Bump, Centered(i, 6, 20), y - FlipBumpRadius, FlipBumpRadius, FlipBumpRadius);
            }
            else
            {
                if (!ChipArray) Rect(Metal, 265, y - 5, 170, 5);
                Rect(Attach, 285, y - 10, 130, ChipArray ? 10 : 5);
                Rect(Die, 285, y - 33, 130, 23);
                Wire(291, y - 33, wireEnd, y, 44); Wire(409, y - 33, 700 - wireEnd, y, 44);
            }
        }
        else
        {
            if (drawMold) Rect(Mold, 185, y - 66, 330, 80);
            Rect(Metal, 265, y - 7, 170, 12);
            Rect(Attach, 285, y - 12, 130, 5);
            Rect(Die, 285, y - 35, 130, 23);
            foreach (bool left in new[] { true, false })
            {
                double x = left ? 185 : 455;
                Rect(Metal, x, y - 7, 60, 12);
                Wire(left ? 291 : 409, y - 35, left ? 230 : 470, y - 7, 38);
                if (Qfn)
                    Rect(Solder, x, y + 5, 60, 9);
                else
                {
                    double edge = left ? 150 : 550;
                    Line(left ? 200 : 500, y - 1, edge, y - 1, Metal, 7);
                    Line(edge, y - 1, edge, y + 34, Metal, 7);
                    Line(edge, y + 34, left ? 120 : 580, y + 34, Metal, 7);
                }
            }
            if (Enabled("thermal_land.enabled"))
                Rect(Solder, 265, y + 5, 170, 9);
        }
    }

    void Plan()
    {
        Rect(Bare ? Die : Bga ? Board : Mold, 200, PlanTop, 300, PlanBottom - PlanTop);
        if (Bare) return;
        if (!Bga)
        {
            double length = Qfn ? 30 : PlanLeadInner + PlanLeadOuter;
            for (int i = 0; i < 6; i++)
            {
                double row = Centered(i, 6, PlanLeadSpacing, PlanCenterY) - 5;
                Rect(Metal, Qfn ? 200 : 200 - PlanLeadOuter, row, length, 10);
                Rect(Metal, Qfn ? 470 : 500 - PlanLeadInner, row, length, 10);
                if (!Sop)
                {
                    double pin = Centered(i, 6, PlanLeadSpacing) - 5;
                    Rect(Metal, pin, Qfn ? PlanTop : PlanTop - PlanLeadOuter, 10, Qfn ? 25 : length);
                    Rect(Metal, pin, Qfn ? PlanBottom - 25 : PlanBottom - PlanLeadInner, 10, Qfn ? 25 : length);
                }
            }
        }
        else if (!Flip)
            Rect(Mold, ChipArray ? 200 : 225, ChipArray ? PlanTop : 390,
                ChipArray ? 300 : 250, ChipArray ? PlanBottom - PlanTop : 160);
        PlanAccessories();
        if (!Flip)
        {
            if (ChipArray) Rect(Attach, 280, 420, 140, 100);
            else Rect(Metal, 265, 408, 170, 124);
            if (!Qfn && !Bga)
            {
                dc.PushClip(new RectangleGeometry(new Rect(200, PlanTop, 300, PlanBottom - PlanTop)));
                foreach (var (x, y) in new[] { (200d, PlanTop), (500d, PlanTop), (200d, PlanBottom), (500d, PlanBottom) })
                    Line(x, y, x < 350 ? 265 : 435, y < PlanCenterY ? 408 : 532, Metal, 6);
                dc.Pop();
            }
        }
        Rect(Die, 285, 426, 130, 88);
        if (!Flip)
            for (int i = 0; i < 6; i++)
            {
                double source = Centered(i, 6, 10), dieY = Centered(i, 6, 12, PlanCenterY);
                double row = Centered(i, 6, Bga ? 21 : PlanLeadSpacing, PlanCenterY);
                Line(285, dieY, Bga ? 235 : 200 + PlanLeadInner, row, WireColor, 1.6);
                Line(415, dieY, Bga ? 465 : 500 - PlanLeadInner, row, WireColor, 1.6);
                if (!Sop)
                {
                    double pin = Centered(i, 6, Bga ? 24 : PlanLeadSpacing);
                    Line(source, 426, pin, Bga ? 395 : PlanTop + PlanLeadInner, WireColor, 1.6);
                    Line(source, 514, pin, Bga ? 545 : PlanBottom - PlanLeadInner, WireColor, 1.6);
                }
            }
        else
            for (int row = 0; row < 3; row++)
                for (int col = 0; col < 6; col++)
                    Ellipse(Bump, Centered(col, 6, 20), Centered(row, 3, 20, PlanCenterY), 3.5, 3.5);
    }

    void PackageSection(bool removeCentralBalls = false)
    {
        bool slug = SlugVisible;
        if (slug) Rect(Mold, 190, SlugSectionTop, 320, SectionY - SlugSectionTop);
        else if (Flip && Value("cover.type") == "encapsulant") Rect(Mold, 195, SectionY - 100, 310, 100);
        Section(SectionY, drawMold: !slug, wireEnd: slug ? 265 : 226, removeCentralBalls: removeCentralBalls);
        CoverSection();
        if (slug) SlugSection();
        if (Wirebond && Enabled("spreader.enabled")) Rect(Metal, 195, SectionY + 21, 310, 9);
    }

    void PackageLegend()
    {
        if (Bare)
        {
            Legend((Die, "芯片"), (Accent, "有源面"), (Bump, "凸点"));
            return;
        }
        var entries = new List<(Brush Color, string Label)>
        {
            (Die, "芯片"), (Bga ? Board : Mold, Bga ? CeramicBoard ? "陶瓷基板" : "基板" : "塑封"),
            (ChipArray ? Mold : Metal, ChipArray ? "塑封" : "金属 / 承载台"),
            (Solder, "焊球 / 焊料"), (Attach, "粘接 / 填充层")
        };
        if (Flip) entries.Add((Bump, "倒装凸点"));
        else entries.Add((WireColor, "键合线"));
        Legend([.. entries]);
    }
}
