namespace PackStudio.Core;

public static class PbgaFcGenerator
{
    public static PackageGeometry Generate(BuildContext c)
    {
        double l = c.N("substrate.length"), w = c.N("substrate.width"), h = c.N("substrate.thickness"), baseZ = c.N("bga.height"), top = baseZ + h;
        double dl = c.N("die.length"), dw = c.N("die.width"), dz = top + c.N("bumps.height");
        c.Center("substrate", "substrate", l, w, h, baseZ, "pbga-substrate", "substrate");
        FlipChipBumps.Build(c, dl, dw, top);
        c.Center("die", "die", dl, dw, c.N("die.thickness"), dz, "silicon", "die");
        Covers.Build(c, dl, dw, top, dz + c.N("die.thickness"));
        Covers.Slug(c, top, false);
        SolderBalls.Build(c);
        Substrate(c, l, w, baseZ, h);
        c.DistributeDiePower();
        var outline = new Footprint(l, w);
        return new(outline, outline, SolderBalls.Footprint(c), Covers.TopFootprint(c), c.Blocks.Max(b => b.Maximum.Z), true);
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
            c.Derived(MaterialMixer.Mix(id, single, dielectric, f, "z"));
            c.Center(id, "via", dl, dw, h, z, id, region, derived: true);
        }

        if (c.B("vias.enabled"))
            Vias.Build(c, metal, matrix, "fc-core-via", baseZ + thickness["lower"], height - thickness["upper"] - thickness["lower"], true);
    }
}
