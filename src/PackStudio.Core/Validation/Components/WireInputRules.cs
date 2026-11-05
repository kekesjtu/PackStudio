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
}
