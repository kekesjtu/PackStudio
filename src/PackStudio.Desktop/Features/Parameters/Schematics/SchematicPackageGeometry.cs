using System.Windows;
using System.Windows.Media;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    const double QfnLeadTop = SectionY - 7, QfnLeadStep = SectionY, QfnLeadBottom = SectionY + 5;
    const double QfnLeadEtch = 12, QfnExposedPadLeft = 300, QfnExposedPadWidth = 100;
    const double QfnViaHeight = 30;

    void Section(double y, bool drawMold = true, double wireEnd = 226, bool removeCentralBalls = false)
    {
        if (Bare)
        {
            Rect(Die, 240, y - 20, 220, 34);
            double activeY = y + (BumpedDie ? 14 : -20);
            if (BumpedDie)
            {
                Rect(Attach, 240, y + 14, 220, 23);
                for (int i = 0; i < 8; i++) Ellipse(Bump, Centered(i, 8, 27), y + 25.5, 11.5, 11.5);
            }
            Line(240, activeY, 460, activeY, Accent, 3);
            return;
        }
        if (Bga)
        {
            if (!Flip && drawMold) Rect(Mold, ChipArray ? 150 : 195, y - 67, ChipArray ? 400 : 310, 67);
            Rect(Board, 150, y, 400, 30);
            if (!CeramicBoard)
            {
                for (int layer = 0; layer < IllustratedLayers; layer++)
                    Rect(Metal, 150, y + 2 + layer * 22.0 / (IllustratedLayers - 1), 400, 3, false);
            }
            if (step == "thermal_vias") ViaSection(y + 5, 19);
            if (HasSolderMask)
            {
                if (ChipArray) Rect(SolderMask, 285, y - 4, 130, 4);
                else
                {
                    Rect(SolderMask, 150, y - 4, 115, 4);
                    Rect(SolderMask, 435, y - 4, 115, 4);
                }
            }
            for (int i = 0; i < 11; i++)
                if (!removeCentralBalls || i is < 4 or > 6)
                    Ellipse(Solder, Centered(i, 11, 36.8), y + 41, 11, 11);
            if (Flip)
            {
                Rect(Die, 285, FlipDieTop(y), 130, 23);
                Rect(Attach, 285, y - 2 * FlipBumpRadius, 130, 2 * FlipBumpRadius);
                for (int i = 0; i < 6; i++) Ellipse(Bump, Centered(i, 6, 20), y - FlipBumpRadius, FlipBumpRadius, FlipBumpRadius);
            }
            else
            {
                if (!ChipArray) Rect(Metal, 265, y, 170, 3);
                Rect(Attach, 285, y - 10, 130, ChipArray ? 6 : 10);
                Rect(Die, 285, y - 33, 130, 23);
                Wire(291, y - 33, wireEnd, y, 44); Wire(409, y - 33, 700 - wireEnd, y, 44);
            }
        }
        else
        {
            if (drawMold) Rect(Mold, 185, y - 66, 330, Qfn ? 71 : 80);
            if (Qfn)
            {
                Rect(Metal, 265, y - 7, 170, 7);
                Rect(Metal, QfnExposedPadLeft, y, QfnExposedPadWidth, 5);
            }
            else
                Rect(Metal, 265, y - 7, 170, ThermalLand ? 21 : 12);
            Rect(Attach, 285, y - 12, 130, 5);
            Rect(Die, 285, y - 35, 130, 23);
            foreach (bool left in new[] { true, false })
            {
                double x = left ? 185 : 455;
                double leadTop = y - (Qfn ? 7 : 13);
                if (Qfn)
                {
                    Rect(Metal, x, leadTop, 60, 7);
                    Rect(Metal, x + (left ? 0 : QfnLeadEtch), y, 60 - QfnLeadEtch, 5);
                }
                else
                    Rect(Metal, x, leadTop, 60, 12);
                Wire(left ? 291 : 409, y - 35, left ? 230 : 470, leadTop, 38);
                if (Qfn)
                    Rect(Solder, x + (left ? 0 : QfnLeadEtch), y + 5, 60 - QfnLeadEtch, 9);
                else
                {
                    double edge = left ? 150 : 550;
                    Line(left ? 200 : 500, y - 1, edge, y - 1, Metal, 7);
                    Line(edge, y - 1, edge, y + 34, Metal, 7);
                    Line(edge, y + 34, left ? 120 : 580, y + 34, Metal, 7);
                }
            }
            if (Qfn && step == "thermal_vias") ViaSection(LandTop, QfnViaHeight);
            if (Qfn || ThermalLand)
                Rect(Solder, Qfn ? QfnExposedPadLeft : 265, LandSolderTop, Qfn ? QfnExposedPadWidth : 170, 9);
            if (ThermalLand)
                Rect(Metal, Qfn ? QfnExposedPadLeft : 265, LandTop, Qfn ? QfnExposedPadWidth : 170, 9);
        }
    }

    double ViaX(int index) => ChipArray ? Centered(2 + index * 2, 11, 36.8) + 18 : Centered(index, 4, 32);

    void ViaSection(double top, double height)
    {
        for (int i = 0; i < 4; i++)
        {
            double x = ViaX(i);
            Rect(Metal, x - 3, top, 6, height);
            Rect(Brushes.White, x - 1, top, 2, height, false);
        }
    }

    void Plan()
    {
        if (QfnBottomView)
        {
            QfnBottomPlan();
            return;
        }
        Rect(Bare ? Die : Bga ? Board : Mold, 200, PlanTop, 300, PlanBottom - PlanTop);
        if (Bare) return;
        if (SpreaderSection)
        {
            Rect(Metal, 200, PlanTop, 300, PlanBottom - PlanTop);
            Rect(Board, 240, 402, 220, 136);
            Rect(Metal, 270, 422, 160, 96);
            return;
        }
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

    void QfnBottomPlan()
    {
        Rect(Mold, 200, PlanTop, 300, PlanBottom - PlanTop);
        for (int i = 0; i < 6; i++)
        {
            double row = Centered(i, 6, PlanLeadSpacing, PlanCenterY) - 5;
            Rect(Metal, 200, row, 30, 10);
            Rect(Metal, 470, row, 30, 10);
            double pin = Centered(i, 6, PlanLeadSpacing) - 5;
            Rect(Metal, pin, PlanTop, 10, 25);
            Rect(Metal, pin, PlanBottom - 25, 10, 25);
        }
        Rect(Metal, 265, 408, 170, 124);
        Rect(Metal, QfnExposedPadLeft, 432, QfnExposedPadWidth, 76);
    }

    void PackageSection(bool removeCentralBalls = false)
    {
        if (CoverType == "encapsulant") Rect(Mold, 195, EncapsulantTop, 310, SectionY - EncapsulantTop);
        Section(SectionY, removeCentralBalls: removeCentralBalls);
        CoverSection();
        if (SpreaderSection)
        {
            Rect(Board, 240, SectionY + 24, 220, 6, false);
            Rect(Metal, 270, SectionY + 21, 160, 9);
        }
    }

    void PackageLegend()
    {
        if (Bare)
        {
            if (BumpedDie) Legend((Die, "芯片"), (Accent, "有源面"), (Bump, "凸点"), (Attach, "底填充"));
            else Legend((Die, "芯片"), (Accent, "有源面"));
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
        if (HasSolderMask) entries.Add((SolderMask, "阻焊层"));
        Legend([.. entries]);
    }
}
