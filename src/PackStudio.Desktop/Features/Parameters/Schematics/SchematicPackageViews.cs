namespace PackStudio.Desktop;

internal sealed partial class SchematicDrawing
{
    void Package()
    {
        if (Bare)
        {
            bool flipped = Checked("die.flipped") || Checked("bumps.enabled");
            Callout("有源面", 150, flipped ? 287 : 145, 240, flipped ? 244 : 210);
        }
        else
        {
            Callout("芯片", 305, 127, 330, Flip ? FlipDieTop(SectionY) + 10 : Bga ? 207 : 205);
            if (Flip)
            {
                if (!Checked("stiffener.enabled"))
                    Callout("倒装凸点", 80, 160, 400, SectionY - FlipBumpRadius);
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
                DimV(235, 244, 435, 555, "thermal_land.thickness");
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
        DimV(Bga ? 163 : 164, Bga ? 230 : 244, Bga ? 505 : 515, 580, Bga ? "encapsulant.thickness" : "body.thickness");
        double left = Bga ? 225 : 200, top = Bga ? 390 : PlanTop, bottom = 2 * PlanCenterY - top;
        string prefix = Bga ? "encapsulant" : "body";
        DimH(left, 700 - left, bottom, PlanLengthDimensionY, prefix + ".length");
        DimV(top, bottom, 700 - left, 548, prefix + ".width");
        SolderMaskDimension();
    }

    void FlagDimensions()
    {
        Callout(Qfn ? "芯片承载焊盘 / DAP" : "承载台 / Die Flag", 350, 290, 350, 228);
        string prefix = Qfn ? "pad" : "flag";
        DimH(265, 435, 408, 345, prefix + ".length");
        DimV(408, 532, 435, 548, prefix + ".width");
        DimensionText("flag.coverage", 350, 585, System.Windows.TextAlignment.Center);
        DimV(223, 235, 435, 560, "flag.thickness");
        DimV(217, 223, 265, 126, "flag.downset", left: true);
        DimensionCallout("tie_bar.width", 78, 398, 229, 388);
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
        DimensionCallout("bond_wire.diameter", 474, 149, 444, 187);
        DimensionText(Bga ? "bond_wire.total" : "bond_wire.count", 350, 306, System.Windows.TextAlignment.Center);
        double left = Bga ? 235 : 200 + PlanLeadInner, right = 700 - left;
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
            DimV(235, 244, 515, 590, "leads.exposed_thickness");
            DimH(455, 515, 235, 291, "leads.length");
            DimensionCallout("leads.etch", 67, 273, 187, 235);
        }
        else
        {
            DimV(229, 264, 550, 600, "leads.height");
            DimV(225.5, 232.5, 155, 122, "leads.thickness", left: true);
            DimH(550, 580, 264, 302, "leads.foot_length");
            DimH(200 + PlanLeadInner, 265, PlanCenterY, PlanBottom - 12,
                Sop ? "leads.gap" : "leads.gap_x");
            DimV(PlanTop + PlanLeadInner, 408, 350, 545, "leads.gap_y");
            DimensionText("leads.coverage", 350, 306, System.Windows.TextAlignment.Center);
        }
        double firstLead = Centered(0, 6, PlanLeadSpacing, PlanCenterY);
        double pitchStart = Sop || Qfn ? firstLead : firstLead + PlanLeadSpacing;
        double widthCenter = Centered(Sop || Qfn ? 2 : 4, 6, PlanLeadSpacing, PlanCenterY);
        double leadEdge = Qfn ? 500 : 520;
        DimV(pitchStart, pitchStart + PlanLeadSpacing, leadEdge, 550, Qfn ? "leads.pitch_y" : "leads.pitch");
        DimV(widthCenter - 5, widthCenter + 5, leadEdge, 570, "leads.width");
        DimH(Centered(0, 6, PlanLeadSpacing), Centered(1, 6, PlanLeadSpacing), PlanTop, 345, "leads.pitch_x");
        BracketV(165, firstLead - 5, Centered(5, 6, PlanLeadSpacing, PlanCenterY) + 5,
            Sop ? "leads.total" : "leads.count_y", 372);
        BracketH(Centered(0, 6, PlanLeadSpacing) - 5, Centered(5, 6, PlanLeadSpacing) + 5,
            PlanBottom + 26, "leads.count_x");
    }

    void Bumps()
    {
        if (Bare)
        {
            DimV(244, 267, 460, 530, "bumps.height");
            DimH(244, 267, 255.5, 305, "bumps.diameter");
            BracketH(244, 456, 339, "bumps.total");
            return;
        }
        DimV(215, 230, 415, 555, "bumps.height");
        DimH(292.5, 307.5, 222.5, 305, "bumps.diameter");
        BracketH(300, 400, 554, "bumps.columns");
        BracketV(254, PlanCenterY - 20, PlanCenterY + 20, "bumps.rows", 444);
        DimensionText("bumps.total", 350, 550, System.Windows.TextAlignment.Center);
    }
}
