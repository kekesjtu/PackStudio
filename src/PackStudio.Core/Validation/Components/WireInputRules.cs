namespace PackStudio.Core;

internal static class WireInputRules
{
    public static void ValidateExtent(InputChecks c, bool accountForDiameter = false)
    {
        foreach (var (dimension, extent) in new[] { ("length", "extent_length"), ("width", "extent_width") })
        {
            string path = "bond_wire." + extent;
            double clearance = accountForDiameter ? 2 * c.N("bond_wire.diameter") : 0;
            string[] paths = accountForDiameter ? [path, "bond_wire.diameter", "die." + dimension] : [path, "die." + dimension];
            c.Check(c.N(path) - clearance <= c.N("die." + dimension), "input.wire.endpoint", "键合线端点必须位于芯片外。", paths);
        }
    }

    public static void Equivalent(InputChecks c, double count, params string[] countPaths)
    {
        double fraction = count * Math.PI * c.N("bond_wire.diameter") / (8 * (c.N("die.length") + c.N("die.width")));
        c.Check(fraction > 1, "input.wire.fraction", "键合线等效体积分数不能超过塑封空间。",
            ["bond_wire.diameter", "die.length", "die.width", .. countPaths]);
    }
}
