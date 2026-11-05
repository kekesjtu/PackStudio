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
            string radial = axis == "x" ? "width" : "length";
            c.Check(c.N("package." + radial) - 2 * c.N("leads.length") - 2 * c.N("leads.etch") <= c.N("die." + radial),
                "input.qfn.wire_endpoint", "QFN 键合线焊盘必须位于芯片外。", "package." + radial, "leads.length", "leads.etch", "die." + radial);
        }
        if (c.B("vias.enabled"))
            foreach (var (dimension, count) in new[] { ("length", "columns"), ("width", "rows") })
                c.Check((c.N("vias." + count) - 1) * c.N("vias.pitch") + c.N("vias.diameter") > c.N("pad.exposed_" + dimension),
                    "input.qfn.via_span", "QFN 通孔必须位于露出焊盘内。", "vias." + count, "vias.pitch", "vias.diameter", "pad.exposed_" + dimension);
    }
}
