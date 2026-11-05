namespace PackStudio.Core;
public static class Wires
{
    public static void FourSides(BuildContext c, double dl, double dw, double xe, double ye, double xv, double yv, double hz, double vz, double vh, string mx, string my, double minHeight = 0, bool xEnabled = true, bool yEnabled = true)
    {
        double d = c.N("bond_wire.diameter");
        foreach (var(axis, end, vertical, die, span, material, enabled)in new[]
        {
            ("x", xe, xv, dl, dw, mx, xEnabled),
            ("y", ye, yv, dw, dl, my, yEnabled)
        }

        )
        {
            if (!enabled)
                continue;
            double radial = end - die / 2;
            if (radial <= 0 || vh < 0)
                throw new ModelGenerationException("generation.wire.geometry", "键合线端点或高度无效。");
            foreach (int sign in new[]
            {
                -1,
                1
            }

            )
            {
                string side = axis == "x" ? (sign == 1 ? "right" : "left") : (sign == 1 ? "upper" : "lower");
                void Add(string part, double start, double r, double z, double h)
                {
                    double position = sign == 1 ? start : -start - r;
                    c.Add($"bond-wire-{part}-{side}", "bond_wire", axis == "x" ? position : -span / 2, axis == "x" ? -span / 2 : position, z, axis == "x" ? r : span, axis == "x" ? span : r, h, material, "bond-wires", derived: true);
                }

                Add("h", die / 2, radial, hz, d);
                if (vh > minHeight)
                    Add("v", vertical, d, vz, vh);
            }
        }
    }

    public static void Equivalent(BuildContext c, string prefix, int count, bool isotropic)
    {
        var mold = c.Component("group-encapsulant", "epoxy-mold");
        var wire = c.Component("group-bond-wires", "gold");
        double fraction = count * Math.PI * c.N("bond_wire.diameter") / (8 * (c.N("die.length") + c.N("die.width")));
        foreach (string axis in new[] { "x", "y" })
            c.Derived(MaterialMixer.Mix(prefix + "-bondwire-" + axis, wire, mold, fraction, isotropic ? "xyz" : axis + "z"));
    }

}
