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
        foreach (var (dimension, axis) in new[] { ("length", "x"), ("width", "y") })
            c.Check(c.N("flag." + dimension) + 2 * c.N(axis == "x" ? gapX : gapY) <= c.N("die." + dimension),
                "input.wire.endpoint", "键合线端点必须位于芯片外。", "flag." + dimension, axis == "x" ? gapX : gapY, "die." + dimension);
    }
}
