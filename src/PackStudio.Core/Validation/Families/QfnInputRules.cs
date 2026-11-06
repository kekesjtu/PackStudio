namespace PackStudio.Core;

internal static class QfnInputRules
{
    public static void Validate(InputChecks c)
    {
        ViaInputRules.Validate(c);
        c.Fits("die.length", "package.length"); c.Fits("die.width", "package.width"); c.Fits("pad.length", "package.length"); c.Fits("pad.width", "package.width");
        c.Check(c.N("leads.exposed_thickness") >= c.N("leads.thickness"), "input.qfn.lead_height", "露出引脚厚度必须小于引脚总厚度。", "leads.exposed_thickness", "leads.thickness");
        c.Check(c.N("leads.count_x") + (double.IsFinite(c.N("leads.count_y")) ? c.N("leads.count_y") : 0) == 0, "input.qfn.lead_count", "QFN 至少需要一组引脚。", "leads.count_x", "leads.count_y");
        foreach (var (axis, dimension) in new[] { ("x", "length"), ("y", "width") })
        {
            if (axis == "y" && !(c.N("leads.count_y") > 0)) continue;
            c.Check((c.N("leads.count_" + axis) - 1) * c.N("leads.pitch_" + axis) + c.N("leads.width") > c.N("package." + dimension),
                "input.qfn.lead_span", "QFN 引脚跨度必须位于封装内。", "leads.count_" + axis, "leads.pitch_" + axis, "leads.width", "package." + dimension);
            c.Check(c.N("package." + dimension) - 2 * c.N("leads.length") - 2 * c.N("leads.etch") <= c.N("die." + dimension),
                "input.qfn.wire_endpoint", "QFN 键合线焊盘必须位于芯片外。", "package." + dimension, "leads.length", "leads.etch", "die." + dimension);
        }
        double wire = c.N("bond_wire.diameter"), steps = c.N("bond_wire.steps");
        foreach (var (axis, transverse) in new[] { ("x", "y"), ("y", "x") })
        {
            double count = c.N("leads.count_" + transverse);
            if (!(count > 0)) continue;
            double die = c.N(axis == "x" ? "die.length" : "die.width"), dt = c.N(axis == "x" ? "die.width" : "die.length");
            double extent = (count - 1) * c.N("leads.pitch_" + transverse) + c.N("leads.width");
            double span = c.N(axis == "x" ? "package.length" : "package.width") / 2 - c.N("leads.length") - c.N("leads.etch") - die / 2;
            double fraction = count * Math.PI * wire * c.N("bond_wire.length_" + axis) / (4 * span * (steps > 1 ? Math.Min(extent, dt) : extent));
            c.Check(fraction > 1, "input.qfn.wire_fraction", "键合线等效体积分数不能超过塑封空间。",
                "bond_wire.diameter", "bond_wire.length_" + axis, "leads.count_" + transverse, "leads.pitch_" + transverse, "leads.width", "die.length", "die.width");
        }
        if (c.B("vias.enabled"))
            foreach (var (dimension, count) in new[] { ("length", "columns"), ("width", "rows") })
                c.Check((c.N("vias." + count) - 1) * c.N("vias.pitch") + c.N("vias.diameter") > c.N("pad.exposed_" + dimension),
                    "input.qfn.via_span", "QFN 通孔必须位于露出焊盘内。", "vias." + count, "vias.pitch", "vias.diameter", "pad.exposed_" + dimension);
    }
}
