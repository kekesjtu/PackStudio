namespace PackStudio.Core;
public static class FlipChip
{
    public static void Bumps(BuildContext c, double lx, double ly, double z)
    {
        int count = c.T("bumps.array_type") == "regular" ? c.I("bumps.columns") * c.I("bumps.rows") : c.I("bumps.total");
        double f = count * Math.PI * Math.Pow(c.N("bumps.diameter"), 2) / (4 * lx * ly);
        var solder = c.Component("group-bump-solder", "solder-pb90");
        var matrix = c.Values["bumps.underfill"]?.Type == Newtonsoft.Json.Linq.JTokenType.Boolean && !c.B("bumps.underfill") ? c.M("static-air") : c.Component("group-underfill", "static-air");
        var m = MaterialLibrary.Mix("flip-chip-bumps-equivalent", solder, matrix, f);
        c.Derived(m with { Conductivity = new(m.Conductivity.Z, m.Conductivity.Z, m.Conductivity.Z) });
        c.Center("flip-chip-bumps-equivalent", "flip_chip_bump", lx, ly, c.N("bumps.height"), z, m.Id, "flip-chip-bumps", derived: true);
        c.Model.Metadata["flip_chip_bump_count"] = count;
    }

    public static void BareDie(BuildContext c)
    {
        double h = c.B("bumps.enabled") ? c.N("bumps.height") : 0;
        if (c.B("bumps.enabled"))
            Bumps(c, c.N("die.length"), c.N("die.width"), 0);
        c.Center("die", "die", c.N("die.length"), c.N("die.width"), c.N("die.thickness"), h, "silicon", "die");
    }

    public static void Build(BuildContext c)
    {
        double l = c.N("substrate.length"), w = c.N("substrate.width"), h = c.N("substrate.thickness"), baseZ = c.N("bga.height"), top = baseZ + h;
        double dl = c.N("die.length"), dw = c.N("die.width"), dz = top + c.N("bumps.height");
        if (dl > l || dw > w)
            throw new ArgumentException("芯片必须位于基板内。");
        c.Center("substrate", "substrate", l, w, h, baseZ, c.Template.Info.Id == "cbga_fc" ? "alumina" : "pbga-substrate", "substrate");
        Bumps(c, dl, dw, top);
        c.Center("die", "die", dl, dw, c.N("die.thickness"), dz, "silicon", "die");
        Covers.Build(c, dl, dw, top, dz + c.N("die.thickness"));
        Covers.Slug(c, top, false);
        SolderBalls.Build(c);
        if (c.Template.Info.Id == "pbga_fc")
            Substrate(c, l, w, baseZ, h);
    }

    static void Substrate(BuildContext c, double l, double w, double baseZ, double height)
    {
        double top = baseZ + height;
        var metal = c.Component("group-metal", "copper");
        var matrix = c.Component("group-substrate", "pbga-substrate");
        MetalLayers.Append(c, MetalLayers.Parse(c, "metal.layers"), l, w, top, metal, matrix, skipZero: true);
        var thickness = new Dictionary<string, double>
        {
            {
                "upper",
                0
            },
            {
                "lower",
                0
            }
        };
        foreach (string region in new[]
        {
            "upper",
            "lower"
        }

        )
        {
            if (!c.B(region + ".enabled"))
                continue;
            var dielectric = c.Component("group-" + region, "pbga-substrate");
            double h = c.N(region + ".thickness"), z = region == "upper" ? top - h : baseZ;
            thickness[region] = h;
            c.Center(region + "-region", "substrate", l, w, h, z, dielectric.Id, region);
            MetalLayers.Append(c, MetalLayers.Parse(c, region + ".layers"), l, w, top, metal, dielectric, region + "trace", true);
            if (c.Values[region + ".count"]?.Type is not (Newtonsoft.Json.Linq.JTokenType.Integer or Newtonsoft.Json.Linq.JTokenType.Float))
                continue;
            double d = c.N(region + ".diameter"), p = c.N(region + ".plating", 0), shell = c.B(region + ".filled") ? 1 : 1 - Math.Pow((d - 2 * p) / d, 2);
            var single = Vias.Hollow(metal, shell, region + "-via-single", true);
            double dl = c.N("die.length"), dw = c.N("die.width"), f = c.I(region + ".count") * Math.PI * d * d / (4 * dl * dw);
            string id = region + "-microvias";
            c.Derived(MaterialLibrary.Mix(id, single, dielectric, f, "z"));
            c.Center(id, "via", dl, dw, h, z, id, region, derived: true);
        }

        if (c.B("vias.enabled"))
            Vias.Build(c, metal, matrix, "fc-core-via", baseZ + thickness["lower"], height - thickness["upper"] - thickness["lower"], true);
    }
}
