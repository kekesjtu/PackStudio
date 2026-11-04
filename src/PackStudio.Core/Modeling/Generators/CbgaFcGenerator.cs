namespace PackStudio.Core;

public static class CbgaFcGenerator
{
    public static PackageGeometry Generate(BuildContext c)
    {
        double l = c.N("substrate.length"), w = c.N("substrate.width"), h = c.N("substrate.thickness"), baseZ = c.N("bga.height"), top = baseZ + h;
        double dl = c.N("die.length"), dw = c.N("die.width"), dz = top + c.N("bumps.height");
        if (dl > l || dw > w)
            throw new ArgumentException("芯片必须位于基板内。");
        c.Center("substrate", "substrate", l, w, h, baseZ, "alumina", "substrate", exposedSurface: true);
        FlipChipBumps.Build(c, dl, dw, top);
        c.Center("die", "die", dl, dw, c.N("die.thickness"), dz, "silicon", "die");
        Covers.Build(c, dl, dw, top, dz + c.N("die.thickness"));
        Covers.Slug(c, top, false);
        SolderBalls.Build(c);
        c.DistributeDiePower();
        var outline = new Footprint(l, w);
        return new(outline, outline, SolderBalls.Footprint(c), Covers.TopFootprint(c), c.Blocks.Max(b => b.Maximum.Z), true);
    }
}
