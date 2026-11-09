namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void Package()
    {
        if (Bare)
        {
            DimH(240, 460, 210, 180, Dimension("芯片长度", "die.length"));
            DimV(210, 244, 460, 500, Dimension("厚度\n", "die.thickness"));
            bool flipped = Enabled("die.flipped") || Enabled("bumps.enabled");
            Callout("有源面", 150, flipped ? 287 : 145, 240, flipped ? 244 : 210);
        }
        else
        {
            Callout("芯片", 305, 127, 330, Flip ? FlipDieTop(SectionY) + 10 : 207);
            if (Flip)
                Callout("倒装凸点", 80, 160, 400, SectionY - FlipBumpRadius);
            else
            {
                Callout("键合线", 490, 127, 444, 187);
                Callout("塑封", 150, 127, 205, 177);
            }
        }
        switch (step)
        {
            case "die" when !Bare:
                double y = Flip ? FlipDieTop(SectionY) : Bga ? 197 : 195;
                if (ChipArray)
                {
                    DimV(y, y + 23, 415, 580, Dimension("芯片厚度\n", "die.thickness"));
                    DimV(y + 23, SectionY, 285, 115, Dimension("粘接层\n", "die.attach"), true);
                }
                else
                {
                    DimV(y, y + 23, 415, Flip ? 555 : 525,
                        Dimension(Flip ? "芯片厚度\n" : "芯片厚度", "die.thickness"));
                    if (!Flip) DimV(y + 23, y + 28, 415, 610, Dimension("粘接层\n", "die.attach"));
                }
                break;
            case "encapsulant":
                DimV(Bga ? 163 : 164, Bga ? 230 : 244, Bga ? 505 : 515, 580,
                    Dimension("塑封厚度\n", Bga || Qfn ? "encapsulant.thickness" : "body.thickness"));
                break;
            case "overall_package" when !Bga:
                DimV(164, 244, 515, 580, Dimension("塑封厚度\n", Qfn ? "encapsulant.thickness" : "body.thickness"));
                break;
            case "die_flag_solder_mask" or "die_flag_tie_bars" or "dap":
                Callout(Qfn ? "芯片承载焊盘 / DAP" : "承载台 / Die Flag", 350, 290, 350, 228);
                break;
            case "thermal_land" or "thermal_land_solder":
                if (Enabled("thermal_land.enabled"))
                    Callout(Dimension("散热焊料厚度", "thermal_land.thickness"), 350, 290, 350, 240);
                break;
            case "bond_wires": Wires(); break;
            case "leadframe" or "lead_solder_interconnect": Leads(); break;
            case "flip_chip_bumps" or "bumped_die": Bumps(); break;
            case "top_cover": TopCover(); break;
            case "backside_spreader": Spreader(); break;
            default:
                if (Bga) DimV(230, 260, 550, 590, Dimension("基板厚度\n", "substrate.thickness"));
                break;
        }
        PackagePlanDimensions();
    }

    void PackagePlanDimensions()
    {
        string length = Bare ? "die.length" : Flip ? "substrate.length" : "package.length";
        bool overview = step == "overall_package" ||
            step == "summary" && template.Steps.All(s => s["key"]?.ToString() != "overall_package");
        if (overview)
        {
            double left = !Bga && !Bare && !Qfn ? 200 - PlanLeadOuter : 200;
            double top = !Bga && !Bare && !Qfn && !Sop ? PlanTop - PlanLeadOuter : PlanTop;
            double bottom = 2 * PlanCenterY - top;
            DimH(left, 700 - left, bottom, PlanLengthDimensionY, Dimension(Bare ? "芯片长度" : "封装长度", length));
            DimV(top, bottom, left, 155, Dimension(Bare ? "宽度\n" : "封装宽度\n", length.Replace("length", "width")), true);
        }
        if (Bare || step is "bond_wires" or "leadframe" or "lead_solder_interconnect" or "top_cover" or "slug" or "backside_spreader") return;
        string key = FlagStep ? Qfn ? "pad.length" : "flag.length" : step == "encapsulant" ? ChipArray ? "package.length" : Bga ? "encapsulant.length" : "body.length" : "die.length";
        double x1 = FlagStep ? 265 : step == "encapsulant" ? Bga && !ChipArray ? 225 : 200 : 285;
        double innerTop = FlagStep ? 408 : step == "encapsulant" ? Bga && !ChipArray ? 390 : PlanTop : 426;
        DimH(x1, 700 - x1, innerTop, 345, Dimension(FlagStep ? "承载台长度" : step == "encapsulant" ? "塑封长度" : "芯片长度", key));
        DimV(FlagStep ? 408 : 426, FlagStep ? 532 : 514, FlagStep ? 435 : 415, 548,
            Dimension(FlagStep ? "承载台宽度\n" : "芯片宽度\n", FlagStep ? Qfn ? "pad.width" : "flag.width" : "die.width"));
    }

    void Wires()
    {
        if (!Bga && !Sop)
            DimH(409, 470, 230, 310, Dimension("键合线长度", "bond_wire.length_x"));
        Callout(Dimension("线径", "bond_wire.diameter"), 80, 155, 253, 185);
        double left = Bga ? 235 : 200 + PlanLeadInner, right = 700 - left, top = Bga ? 395 : PlanTop + PlanLeadInner;
        if (!Sop)
        {
            DimH(left, right, 2 * PlanCenterY - top, PlanLengthDimensionY, Dimension("线阵列长度", "bond_wire.extent_length", "lbwx"));
            DimV(top, 2 * PlanCenterY - top, right, 565, Dimension("线阵列宽度\n", "bond_wire.extent_width", "lbwy"));
        }
    }

    void Leads()
    {
        if (Qfn)
        {
            DimV(223, 235, 515, 562, Dimension("引脚厚度\n", "leads.thickness"));
            DimH(455, 515, 235, 291, Dimension("外露长度", "leads.length"));
            DimH(200, 230, Centered(1, 6, PlanLeadSpacing, PlanCenterY), 345, Dimension("外露长度", "leads.length"));
        }
        else
        {
            DimV(229, 264, 550, 595, Dimension("引脚高度\n", "leads.height"));
            DimH(550, 580, 264, 302, Dimension("引脚足长", "leads.foot_length"));
            Line(200 + PlanLeadInner, 470, 265, 470);
            Arrow(200 + PlanLeadInner, 470, 1, 0, length: 4); Arrow(265, 470, -1, 0, length: 4);
            Callout(Dimension("框架间隙", "leads.gap", "g1"), 155, 440, 255, 470, right: true);
        }
        double firstLead = Centered(0, 6, PlanLeadSpacing, PlanCenterY);
        double thirdLead = Centered(2, 6, PlanLeadSpacing, PlanCenterY);
        double leadEdge = Qfn ? 500 : 520;
        DimV(firstLead, firstLead + PlanLeadSpacing, leadEdge, 558, Dimension("节距\n", Qfn ? "leads.pitch_y" : "leads.pitch"));
        DimV(thirdLead - 5, thirdLead + 5, leadEdge, 594, Dimension("线宽\n", "leads.width"));
        double columnTop = Centered(0, 6, PlanLeadSpacing, PlanCenterY) - 5;
        double columnBottom = Centered(5, 6, PlanLeadSpacing, PlanCenterY) + 5;
        string columns = Symbol("leads.count_y").Length > 0
            ? Dimension("左右侧引脚数", "leads.count_y")
            : Dimension("引脚总数", "leads.total");
        BracketV(165, columnTop, columnBottom, columns, 372);
        if (Symbol("leads.count_x").Length > 0)
            BracketH(Centered(0, 6, PlanLeadSpacing) - 5, Centered(5, 6, PlanLeadSpacing) + 5,
                PlanBottom + 26, Dimension("上下侧引脚数", "leads.count_x"));
    }

    void Bumps()
    {
        if (Bare)
        {
            if (!Enabled("bumps.enabled")) return;
            DimV(244, 267, 460, 530, Dimension("凸点高度\n", "bumps.height"));
            DimH(244, 267, 255.5, 305, Dimension("凸点直径", "bumps.diameter"));
        }
        else
        {
            DimV(215, 230, 415, 555, Dimension("凸点高度\n", "bumps.height"));
            DimH(292.5, 307.5, 222.5, 305, Dimension("凸点直径", "bumps.diameter"));
        }
    }
}
