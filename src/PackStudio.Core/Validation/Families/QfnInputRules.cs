namespace PackStudio.Core;

internal static class QfnInputRules
{
    public static void Validate(InputChecks c)
    {
        ViaInputRules.Validate(c);
        c.Fits("die.length", "package.length"); c.Fits("die.width", "package.width"); c.Fits("pad.length", "package.length"); c.Fits("pad.width", "package.width");
        c.Check(c.N("leads.exposed_thickness") >= c.N("leads.thickness"), "input.qfn.lead_height", "露出引脚厚度必须小于引脚总厚度。", "leads.exposed_thickness", "leads.thickness");
        c.Check(c.N("leads.count_x") + (double.IsFinite(c.N("leads.count_y")) ? c.N("leads.count_y") : 0) == 0, "input.qfn.lead_count", "QFN 至少需要一组引脚。", "leads.count_x", "leads.count_y");
        c.Check(c.N("leads.thickness") + c.N("die.attach") + c.N("die.thickness") > c.N("encapsulant.thickness") + 1e-10,
            "input.encapsulant.stack", "塑封必须覆盖载片台、粘接层和芯片。", "leads.thickness", "die.attach", "die.thickness", "encapsulant.thickness");
        double wire = c.N("bond_wire.diameter"), steps = c.N("bond_wire.steps");
        foreach (var row in QfnLeadLayout.Rows(c.N))
        {
            string countKey = "leads.count_" + row.RowAxis, pitchKey = "leads.pitch_" + row.RowAxis;
            c.Check(row.Count > 1 && c.N("leads.width") > row.Pitch, "input.qfn.pitch", "同排引脚宽度不能大于节距。", countKey, pitchKey, "leads.width");
            c.Check(row.Extent > c.N("package." + row.RowDimension), "input.qfn.lead_span", "QFN 引脚跨度必须位于封装内。",
                countKey, pitchKey, "leads.width", "package." + row.RowDimension);
            c.Check(row.WireSpan <= 0, "input.qfn.wire_endpoint", "QFN 键合线焊盘必须位于芯片外。",
                countKey, "package." + row.RadialDimension, "leads.length", "leads.etch", "die." + row.RadialDimension);
            string wireLength = "bond_wire.length_" + row.RadialAxis;
            double transverseWidth = steps > 1 ? Math.Min(row.Extent, row.TransverseDie) : row.Extent;
            double fraction = row.Count * Math.PI * wire * c.N(wireLength) / (4 * row.WireSpan * transverseWidth);
            c.Check(fraction > 1, "input.qfn.wire_fraction", "键合线等效体积分数不能超过塑封空间。",
                "bond_wire.diameter", wireLength, countKey, pitchKey, "leads.width", "die.length", "die.width",
                "package." + row.RadialDimension, "leads.length", "leads.etch", "bond_wire.steps");
        }
        if (c.B("vias.enabled"))
            foreach (var (dimension, count) in new[] { ("length", "columns"), ("width", "rows") })
                c.Check((c.N("vias." + count) - 1) * c.N("vias.pitch") + c.N("vias.diameter") > c.N("pad.exposed_" + dimension),
                    "input.qfn.via_span", "QFN 通孔必须位于露出焊盘内。", "vias." + count, "vias.pitch", "vias.diameter", "pad.exposed_" + dimension);
    }
}
