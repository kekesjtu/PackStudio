namespace PackStudio.Core;

public static class BareDieGenerator
{
    public static PackageGeometry Generate(BuildContext c)
    {
        double h = c.B("bumps.enabled") ? c.N("bumps.height") : 0;
        if (c.B("bumps.enabled"))
            FlipChipBumps.Build(c, c.N("die.length"), c.N("die.width"), 0);
        c.Center("die", "die", c.N("die.length"), c.N("die.width"), c.N("die.thickness"), h, "silicon", "die");
        c.DistributeDiePower();
        var outline = new Footprint(c.N("die.length"), c.N("die.width"));
        return new(outline, outline, outline, outline, c.N("die.thickness"), c.B("die.flipped") || c.B("bumps.enabled"));
    }
}
