namespace PackStudio.Core;

internal static class LeadframeInputRules
{
    public static void Validate(InputChecks c, string flagThickness, string gapX, string gapY)
    {
        c.Fits("body.width", "package.width");
        c.Fits("body.length", "package.length");
        foreach (string dimension in new[] { "length", "width" })
        { c.Fits("flag." + dimension, "body." + dimension); c.Fits("die." + dimension, "body." + dimension); }
        double flagHeight = c.N(flagThickness);
        c.Check(c.N("leads.height") - c.N("flag.downset") + flagHeight + c.N("die.attach") + c.N("die.thickness") > c.N("body.thickness"),
            "input.leadframe.stack", "芯片堆叠必须位于塑封内。", "leads.height", "flag.downset", flagThickness, "die.attach", "die.thickness", "body.thickness");
        if (c.B("thermal_land.enabled")) c.Check(c.N("package.standoff") <= 0, "input.thermal_land", "散热焊盘焊料需要正的离地高度。", "package.standoff");
        c.Check(c.N("leads.width") > c.N("leads.pitch"), "input.leadframe.pitch", "引脚宽度不能大于节距。", "leads.width", "leads.pitch");
        foreach (var (dimension, axis) in new[] { ("length", "x"), ("width", "y") })
        {
            string gap = axis == "x" ? gapX : gapY;
            c.Check(c.N("flag." + dimension) + 2 * c.N(gap) <= c.N("die." + dimension),
                "input.wire.endpoint", "键合线端点必须位于芯片外。", "flag." + dimension, gap, "die." + dimension);
            c.Check(c.N("body." + dimension) - c.N("flag." + dimension) - 2 * c.N(gap) <= 0,
                "input.leadframe.gap", "引脚内端必须位于塑封体内。", "body." + dimension, "flag." + dimension, gap);
        }
    }
}
