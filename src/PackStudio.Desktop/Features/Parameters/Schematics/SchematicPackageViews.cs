namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void Package()
    {
        if (Bare)
        {
            Callout("有源面", 150, BumpedDie ? 287 : 145, 240, BumpedDie ? 244 : 210);
        }
        else
        {
            Callout("芯片", 305, CoverType == "encapsulant" ? 105 : 127, 330, Flip ? FlipDieTop(SectionY) + 10 : Bga ? 207 : 205);
            if (Flip)
            {
                if (!StiffenedLid) Callout("倒装凸点", 80, 160, 400, SectionY - FlipBumpRadius);
            }
            else
            {
                if (Field("bond_wire.diameter") == null)
                    Callout("键合线", 490, 127, 444, 187);
                Callout("塑封", 150, 127, 205, 177);
            }
        }

        switch (step)
        {
            case "overall_package" or "package_substrate":
                PackageOutline();
                break;
            case "die":
                DieDimensions();
                break;
            case "encapsulant":
                EncapsulantDimensions();
                break;
            case "die_flag_solder_mask" or "die_flag_tie_bars" or "dap":
                FlagDimensions();
                break;
            case "thermal_land" or "thermal_land_solder":
                Callout("焊料", 470, 277, 430, LandSolderTop + 4.5, arrow: true);
                Callout("散热焊盘", 290, 292, 350, LandTop + 4.5, arrow: true);
                DimV(LandTop, LandTop + 9, 435, 575, "thermal_land.thickness");
                break;
            case "bond_wires": Wires(); break;
            case "leadframe" or "lead_solder_interconnect": Leads(); break;
            case "flip_chip_bumps" or "bumped_die": Bumps(); break;
            case "top_cover": TopCover(); break;
            case "backside_spreader": Spreader(); break;
        }
    }

    void PackageOutline()
    {
        double left = !Bga && !Qfn ? 200 - PlanLeadOuter : 200;
        double top = !Bga && !Qfn && !Sop ? PlanTop - PlanLeadOuter : PlanTop;
        double bottom = 2 * PlanCenterY - top;
        string prefix = Flip ? "substrate" : "package";
        DimH(left, 700 - left, bottom, PlanLengthDimensionY, prefix + ".length");
        DimV(top, bottom, left, 155, prefix + ".width", left: true);
        DimV(230, 260, 550, 590, "substrate.thickness");
        DimV(164, 244, 515, 580, "encapsulant.thickness");
        DimV(Qfn ? 235 : 244, Qfn ? 244 : 264, Qfn ? 515 : 580, Qfn ? 580 : 610, "package.standoff");
    }

    void DieDimensions()
    {
        if (Bare)
        {
            DimV(210, 244, 460, 500, "die.thickness");
            DimH(200, 500, PlanTop, 345, "die.length");
            DimV(PlanTop, PlanBottom, 500, 548, "die.width");
            return;
        }
        double top = Flip ? FlipDieTop(SectionY) : Bga ? 197 : 195;
        DimV(top, top + 23, 415, 555, "die.thickness");
        DimV(top + 23, ChipArray ? SectionY : top + 28, 285, 115, "die.attach", left: true);
        DimH(285, 415, 426, 345, "die.length");
        DimV(426, 514, 415, 548, "die.width");
        if (Bga && !Flip && !ChipArray) Wires();
    }

    void EncapsulantDimensions()
    {
        DimV(Bga ? 163 : 164, Bga ? 230 : Qfn ? 235 : 244, Bga ? 505 : 515, 580, Bga || Qfn ? "encapsulant.thickness" : "body.thickness");
        double left = Bga ? 225 : 200, top = Bga ? 390 : PlanTop, bottom = 2 * PlanCenterY - top;
        string prefix = Bga ? "encapsulant" : "body";
        DimH(left, 700 - left, bottom, PlanLengthDimensionY, prefix + ".length");
        DimV(top, bottom, 700 - left, 548, prefix + ".width");
        SolderMaskDimension();
    }

    void FlagDimensions()
    {
        Callout(Qfn ? "芯片承载焊盘 / DAP" : "承载台 / Die Flag", 420, 290, 374, 228);
        string prefix = Qfn ? "pad" : "flag";
        DimH(265, 435, 408, 345, prefix + ".length");
        DimV(408, 532, 435, 548, prefix + ".width");
        DimensionText("flag.coverage", 350, 603, System.Windows.TextAlignment.Center);
        DimV(223, 235, 435, 560, "flag.thickness");
        DimV(217, 223, 265, 126, "flag.downset", left: true);
        DimensionCallout("tie_bar.width", 65, 328, 229, 388);
        SolderMaskDimension();
        if (Qfn)
        {
            DashedRect(312, 432, 76, 76);
            DimH(312, 388, 508, PlanLengthDimensionY, "pad.exposed_length");
            DimV(432, 508, 312, 153, "pad.exposed_width", left: true);
        }
    }

    void SolderMaskDimension()
    {
        if (Field("solder_mask.thickness") == null) return;
        Rect(Mold, 150, 230, 65, 4);
        DimV(230, 234, 150, 120, "solder_mask.thickness", left: true);
    }

    void Wires()
    {
        DimensionCallout("bond_wire.diameter", 474, 123, 444, 187);
        double left = Bga ? 235 : 200 + PlanLeadInner, right = 700 - left;
        if (Dimension(Bga ? "bond_wire.total" : "bond_wire.count") is { } count)
        {
            double first = Centered(0, 6, Bga ? 21 : PlanLeadSpacing, PlanCenterY) - 7;
            double last = Centered(5, 6, Bga ? 21 : PlanLeadSpacing, PlanCenterY) + 7;
            double boxLeft = left + 5, boxRight = right - 5;
            DashedRect(boxLeft, first, 285 - boxLeft, last - first);
            DashedRect(415, first, boxRight - 415, last - first);
            Text(count, 350, 310, align: System.Windows.TextAlignment.Center);
            Line(350, 331, 350, 345);
            double leftTarget = (boxLeft + 285) / 2, rightTarget = (415 + boxRight) / 2;
            Line(leftTarget, 345, rightTarget, 345);
            Line(leftTarget, 345, leftTarget, first);
            Line(rightTarget, 345, rightTarget, first);
            Arrow(leftTarget, first, 0, -1);
            Arrow(rightTarget, first, 0, -1);
        }
        double top = Bga ? 395 : PlanTop + PlanLeadInner, bottom = 2 * PlanCenterY - top;
        string length = Bga ? "bond_wire.extent_length" : "bond_wire.length_x";
        string width = Bga ? "bond_wire.extent_width" : "bond_wire.length_y";
        DimH(left, right, bottom, Bga && !ChipArray ? 570 : PlanLengthDimensionY, length);
        DimV(top, bottom, right, Bga && !ChipArray ? 620 : 565, width);
    }

    void Leads()
    {
        if (Qfn)
        {
            DimV(223, 235, 185, 140, "leads.thickness", left: true);
            DimV(230, 235, 515, 590, "leads.exposed_thickness");
            DimH(455, 515, 235, 291, "leads.length");
            DimensionCallout("leads.etch", 67, 273, 187, 235);
        }
        else
        {
            DimV(229, 264, 550, 600, "leads.height");
            DimV(225.5, 232.5, 155, 122, "leads.thickness", left: true);
            DimH(550, 580, 264, 302, "leads.foot_length");
            DimH(200 + PlanLeadInner, 265, PlanCenterY, 325,
                Sop ? "leads.gap" : "leads.gap_x");
            DimV(PlanTop + PlanLeadInner, 408, 350, 545, "leads.gap_y");

        }
        double firstLead = Centered(0, 6, PlanLeadSpacing, PlanCenterY);
        double pitchStart = Sop || Qfn ? firstLead : firstLead + PlanLeadSpacing;
        double widthCenter = Centered(Sop || Qfn ? 2 : 4, 6, PlanLeadSpacing, PlanCenterY);
        double leadEdge = Qfn ? 500 : 520;
        DimV(pitchStart, pitchStart + PlanLeadSpacing, leadEdge, 550, Qfn ? "leads.pitch_y" : "leads.pitch");
        DimV(widthCenter - 5, widthCenter + 5, leadEdge, 570, "leads.width");
        DimH(Centered(0, 6, PlanLeadSpacing), Centered(1, 6, PlanLeadSpacing), PlanTop, 345, "leads.pitch_x");
        double lastLead = Centered(5, 6, PlanLeadSpacing, PlanCenterY);
        if (Sop) DimV(firstLead - 5, lastLead + 5, 180, 165, "leads.total", left: true);
        else BracketV(165, firstLead - 5, lastLead + 5, "leads.count_y", 372);
        BracketH(Centered(0, 6, PlanLeadSpacing) - 5, Centered(5, 6, PlanLeadSpacing) + 5,
            PlanBottom + 26, "leads.count_x");
    }

    void Bumps()
    {
        if (Bare)
        {
            DimV(244, 267, 460, 530, "bumps.height");
            DimH(244, 267, 255.5, 300, "bumps.diameter");
            DimensionCallout("bumps.total", 520, 282, 456, 256, arrow: true);
            return;
        }
        DimV(215, 230, 415, 555, "bumps.height");
        DimH(292.5, 307.5, 222.5, 305, "bumps.diameter");
        Line(300, PlanCenterY + 25, 300, PlanBottom + 20);
        Line(400, PlanCenterY + 25, 400, PlanBottom + 20);
        BracketH(300, 400, PlanBottom + 15, "bumps.columns");
        Line(295, PlanCenterY - 20, 179, PlanCenterY - 20);
        Line(295, PlanCenterY + 20, 179, PlanCenterY + 20);
        BracketV(184, PlanCenterY - 20, PlanCenterY + 20, "bumps.rows", 444);
        DashedRect(291, PlanCenterY - 28, 118, 56);
        DimensionCallout("bumps.total", 526, 490, 409, PlanCenterY + 18, arrow: true);
    }
}
