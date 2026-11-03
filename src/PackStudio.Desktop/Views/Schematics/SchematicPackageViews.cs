using System.Windows.Media;

namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void Section(double y)
    {
        if (Bare)
        {
            Rect(Die, 240, y - 20, 220, 34);
            double activeY = y + (Enabled("die.flipped") ? 14 : -20);
            Line(240, activeY, 460, activeY, Accent, 3);
            if (Enabled("bumps.enabled"))
            {
                Rect(Attach, 240, y + 14, 220, 23);
                for (int i = 0; i < 8; i++) Ellipse(Solder, 254 + i * 27, y + 25, 9, 10);
            }
            return;
        }
        if (Bga)
        {
            if (!Flip) Rect(Mold, 195, y - 67, 310, 67);
            Rect(family == "cbga_fc" ? Cover : Substrate, 150, y, 400, 30);
            if (family != "cbga_fc")
            {
                Rect(Metal, 150, y + 2, 400, 3, false);
                Rect(Metal, 150, y + 24, 400, 3, false);
            }
            for (int i = 0; i < 11; i++) Ellipse(Solder, 166 + i * 36.8, y + 44, 10, 11);
            if (Flip)
            {
                Rect(Die, 285, y - 48, 130, 23);
                if (Enabled("bumps.underfill")) Rect(Attach, 285, y - 25, 130, 25);
                for (int i = 0; i < 6; i++) Ellipse(Solder, 295 + i * 22, y - 12, 7, 9);
            }
            else
            {
                Rect(Metal, 265, y - 5, 170, 5);
                Rect(Attach, 285, y - 10, 130, 5);
                Rect(Die, 285, y - 33, 130, 23);
                Wire(291, y - 33, 226, y, 44); Wire(409, y - 33, 474, y, 44);
            }
        }
        else
        {
            Rect(Mold, 185, y - 66, 330, 80);
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
                    double edge = left ? 148 : 550;
                    Line(left ? 200 : 500, y - 1, edge, y - 1, Metal, 7);
                    Line(edge, y - 1, edge, y + 34, Metal, 7);
                    Line(edge, y + 34, left ? 120 : 580, y + 34, Metal, 7);
                }
            }
            if (step is "thermal_land" or "thermal_land_solder" || Enabled("thermal_land.enabled"))
                Rect(Solder, 265, y + 5, 170, 9);
        }
    }

    void Plan()
    {
        Rect(Bare ? Die : Bga ? family == "cbga_fc" ? Cover : Substrate : Mold, 200, 390, 300, 160);
        if (Bare) return;
        if (!Bga)
        {
            for (int i = 0; i < 6; i++)
            {
                double y = 400 + i * 26;
                Rect(Metal, Qfn ? 200 : 180, y, Qfn ? 30 : 50, 10);
                Rect(Metal, 470, y, Qfn ? 30 : 50, 10);
                if (!Sop)
                {
                    double x = 218 + i * 48;
                    Rect(Metal, x, Qfn ? 390 : 370, 10, Qfn ? 25 : 45);
                    Rect(Metal, x, 525, 10, Qfn ? 25 : 45);
                }
            }
        }
        else if (!Flip)
            Rect(Mold, 225, 405, 250, 130);
        if (!Flip)
        {
            Rect(Metal, 265, 420, 170, 100);
            if (FlagStep && !Qfn && !Bga)
                foreach (var (x, y) in new[] { (200d, 390d), (500d, 390d), (200d, 550d), (500d, 550d) })
                    Line(x, y, x < 350 ? 265 : 435, y < 470 ? 420 : 520, Metal, 8);
        }
        Rect(Die, 285, 435, 130, 70);
        if (step == "die") Outline(281, 431, 138, 78);
        if (FlagStep) Outline(261, 416, 178, 108);
    }

    void Package()
    {
        Section(230);
        if (Bare)
        {
            DimH(240, 460, 210, 180, Dimension("芯片长度", "die.length"));
            DimV(210, 244, 460, 500, Dimension("厚度\n", "die.thickness"));
            Text(Enabled("die.flipped") ? "有源面朝下（翻转芯片）" : "有源面朝上", 350, 287, 13, align: System.Windows.TextAlignment.Center);
        }
        else
        {
            Callout("芯片", 305, 127, 330, Flip ? 192 : 207);
            if (Flip)
                Callout("倒装凸点", 485, 147, 405, 218);
            else
            {
                Callout("键合线", 490, 127, 444, 187);
                Callout("塑封", 150, 127, 205, 177);
            }
            if (step == "die")
            {
                double y = Flip ? 182 : 195;
                DimV(y, y + 23, 415, 555, Dimension("芯片厚度\n", "die.thickness"));
                if (!Flip) Callout(Dimension("粘接层", "die.attach"), 155, 295, 295, 220);
            }
            else if (step is "encapsulant" or "overall_package")
                DimV(164, 244, 515, 580, Dimension("塑封厚度\n", Bga ? "encapsulant.thickness" : Qfn ? "encapsulant.thickness" : "body.thickness"));
            else if (FlagStep)
                Callout(Qfn ? "芯片承载焊盘 / DAP" : "承载台 / Die Flag", 350, 290, 350, 228);
            else if (step is "thermal_land" or "thermal_land_solder")
                Callout(Dimension("散热焊料厚度", "thermal_land.thickness"), 350, 290, 350, 240);
            else if (Bga)
                DimV(230, 260, 550, 590, Dimension("基板厚度\n", "substrate.thickness"));
            else
                Callout("引线框", 130, 295, 200, 229);
        }
        Plan();
        string length = Bare ? "die.length" : Bga ? Flip ? "substrate.length" : "package.length" : "package.length";
        string width = length.Replace("length", "width");
        double left = !Bga && !Bare && !Qfn ? 180 : 200;
        double top = !Bga && !Bare && !Qfn && !Sop ? 370 : 390;
        double bottom = 940 - top;
        DimH(left, 700 - left, bottom, 579, Dimension(Bare ? "芯片长度" : "封装长度", length));
        DimV(top, bottom, left, 155, Dimension(Bare ? "宽度\n" : "封装宽度\n", width), true);
        if (!Bare)
        {
            string key = FlagStep ? Qfn ? "pad.length" : "flag.length" : step == "encapsulant" ? Bga ? "encapsulant.length" : "body.length" : "die.length";
            double x1 = FlagStep ? 265 : step == "encapsulant" ? Bga ? 225 : 200 : 285, x2 = 700 - x1;
            DimH(x1, x2, 420, 368, Dimension(FlagStep ? "承载台长度" : step == "encapsulant" ? "塑封长度" : "芯片长度", key));
            DimV(FlagStep ? 420 : 435, FlagStep ? 520 : 505, FlagStep ? 435 : 415, 548,
                Dimension(FlagStep ? "承载台宽度\n" : "芯片宽度\n", FlagStep ? Qfn ? "pad.width" : "flag.width" : "die.width"));
        }
        Axes(70, 554);
        if (Bare)
            Legend((Die, "芯片"), (Accent, "有源面"), (Solder, "可选凸点"));
        else
            Legend((Die, "芯片"), (Bga ? family == "cbga_fc" ? Cover : Substrate : Mold,
                Bga ? family == "cbga_fc" ? "陶瓷基板" : "基板" : "塑封"), (Metal, "金属 / 承载台"),
                (Solder, "焊球 / 焊料"), (Attach, "粘接 / 填充层"));
    }

    void Wires()
    {
        Section(260);
        Callout("键合线", 470, 136, 447, 221);
        DimH(291, 474, 260, 335, Dimension("名义路径 / 跨度", Bga ? "bond_wire.extent_length" : "bond_wire.length_x"));
        Callout(Dimension("线径", "bond_wire.diameter"), 170, 139, 253, 215);
        Rect(Brush("#F0F4F8"), 205, 430, 290, 115);
        Rect(Metal, 270, 445, 160, 85);
        Rect(Die, 290, 452, 120, 70);
        for (int i = 0; i < 7; i++)
        {
            double x = 297 + i * 17;
            Line(x, 452, 220 + i * 43, 430, Ink, 1.4);
            Line(x, 522, 220 + i * 43, 545, Ink, 1.4);
        }
        Outline(212, 422, 276, 132);
        DimH(212, 488, 430, 406, Sop ? "名义路径 X" : Dimension("线阵列长度", "bond_wire.extent_length", "lbwx"));
        DimV(422, 554, 488, 540, Sop ? "名义路径 Y" : Dimension("线阵列宽度\n", "bond_wire.extent_width", "lbwy"));
        Axes(105, 550);
        Legend((Die, "芯片"), (Metal, "键合线 / 焊盘"), (Mold, "塑封"));
    }
}
