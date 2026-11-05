namespace PackStudio.Core;

internal static class BumpInputRules
{
    public static void Validate(InputChecks c)
    {
        double count = c.T("bumps.array_type") == "regular" ? c.N("bumps.columns") * c.N("bumps.rows") : c.N("bumps.total");
        double fraction = count * Math.PI * Math.Pow(c.N("bumps.diameter"), 2) / (4 * c.N("die.length") * c.N("die.width"));
        c.Check(fraction > 1, "input.bumps.fraction", "凸点总体积比例不能超过芯片覆盖区域。", "bumps.diameter", "bumps.total", "bumps.columns", "bumps.rows", "die.length", "die.width");
    }
}
