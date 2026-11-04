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
        Rect(Bare ? Die : Bga ? Board : Mold, 200, 390, 300, 160);
        if (Bare) return;
        if (!Bga)
        {
            for (int i = 0; i < 6; i++)
            {
                double y = Centered(i, 6, 26, 470) - 5;
                Rect(Metal, Qfn ? 200 : 180, y, Qfn ? 30 : 50, 10);
                Rect(Metal, 470, y, Qfn ? 30 : 50, 10);
                if (!Sop)
                {
                    double x = Centered(i, 6, 48) - 5;
                    double height = Qfn ? 25 : 20;
                    Rect(Metal, x, Qfn ? 390 : 370, 10, height);
                    Rect(Metal, x, Qfn ? 525 : 550, 10, height);
                }
            }
        }
        else if (!Flip)
            Rect(Mold, ChipArray ? 200 : 225, ChipArray ? 390 : 405,
                ChipArray ? 300 : 250, ChipArray ? 160 : 130);
        PlanAccessories();
        if (!Flip)
        {
            if (ChipArray) Rect(Attach, 280, 430, 140, 80);
            else Rect(Metal, 265, 420, 170, 100);
            if (!Qfn && !Bga)
                foreach (var (x, y) in new[] { (200d, 390d), (500d, 390d), (200d, 550d), (500d, 550d) })
                    Line(x, y, x < 350 ? 265 : 435, y < 470 ? 420 : 520, Metal, 8);
        }
        Rect(Die, 285, 435, 130, 70);
        if (!Bga && !Qfn)
            for (int i = 0; i < 6; i++)
            {
                double outer = Centered(i, 6, 26, 470), inner = Centered(i, 6, 17, 470);
                Line(230, outer, 245, inner, Metal, 3); Line(470, outer, 455, inner, Metal, 3);
                if (!Sop)
                {
                    double pin = Centered(i, 6, 48), finger = Centered(i, 6, 24);
                    Line(pin, 390, finger, 400, Metal, 3); Line(pin, 550, finger, 540, Metal, 3);
                }
            }
        if (!Flip)
            for (int i = 0; i < 6; i++)
            {
                double source = Centered(i, 6, 10), end = Centered(i, 6, 17, 470);
                Line(285, 470 + source - 350, Bga ? 235 : 245, end, WireColor, 1.6);
                Line(415, 470 + source - 350, Bga ? 465 : 455, end, WireColor, 1.6);
                if (!Sop)
                {
                    double pin = Centered(i, 6, 24);
                    Line(source, 435, pin, Bga ? 410 : 400, WireColor, 1.6);
                    Line(source, 505, pin, Bga ? 530 : 540, WireColor, 1.6);
                }
            }
        else
            for (int row = 0; row < 3; row++)
                for (int col = 0; col < 6; col++)
                    Ellipse(Bump, Centered(col, 6, 20), Centered(row, 3, 20, 470), 3.5, 3.5);
    }

    void PackageSection(bool removeCentralBalls = false)
    {
        bool slug = SlugVisible;
        if (slug) Rect(Mold, 190, SectionY - 125, 320, 125);
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
