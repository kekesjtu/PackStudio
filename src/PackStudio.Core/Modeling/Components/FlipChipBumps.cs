namespace PackStudio.Core;

public static class FlipChipBumps
{
    public static void Build(BuildContext c, double lx, double ly, double z)
    {
        int count = c.T("bumps.array_type") == "regular" ? c.I("bumps.columns") * c.I("bumps.rows") : c.I("bumps.total");
        double f = count * Math.PI * Math.Pow(c.N("bumps.diameter"), 2) / (4 * lx * ly);
        var solder = c.Component("group-bump-solder", "solder-pb90");
        var matrix = c.Values["bumps.underfill"]?.Type == Newtonsoft.Json.Linq.JTokenType.Boolean && !c.B("bumps.underfill") ? c.M("static-air") : c.Component("group-underfill", "static-air");
        var m = MaterialMixer.Mix("flip-chip-bumps-equivalent", solder, matrix, f);
        c.Derived(m with { Conductivity = new(m.EffectiveConductivity.Z, m.EffectiveConductivity.Z, m.EffectiveConductivity.Z), ConductType = 0 });
        c.Center("flip-chip-bumps-equivalent", "flip_chip_bump", lx, ly, c.N("bumps.height"), z, m.Id, "flip-chip-bumps", derived: true);
        c.FlipChipBumpCount = count;
    }

}
