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
                throw new ArgumentException("键合线端点或高度无效。");
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

    public static void Coupled(BuildContext c)
    {
        string template = c.Template.Info.Id;
        if (template is not ("chip_array" or "pbga_wb" or "sop" or "pqfp"))
            return;
        var mold = c.Component("group-encapsulant", "epoxy-mold");
        var wire = c.Component("group-bond-wires", "gold");
        double d = c.N("bond_wire.diameter"), dl = c.N("die.length"), dw = c.N("die.width");
        string prefix = template == "pbga_wb" ? "wirebond" : template == "chip_array" ? "chip-array" : template;
        int count = template == "chip_array" ? (c.B("bond_wire.auto_count") ? SolderBalls.WireCount(c) : c.I("bond_wire.total")) : c.I(template == "pbga_wb" ? "bond_wire.total" : "bond_wire.count");
        foreach (string axis in new[]
        {
            "x",
            "y"
        }

        )
        {
            double fraction = count * Math.PI * d / (8 * (dl + dw));
            if (template == "pqfp")
            {
                double transverse = axis == "x" ? dw : dl, die = axis == "x" ? dl : dw, flag = c.N(axis == "x" ? "flag.length" : "flag.width");
                double vertical = Math.Abs(LeadframeStack.Evaluate(c.Values, false).WireHeight);
                double span = (flag - die) / 2 + c.N("leads.gap_" + axis) + vertical;
                fraction = (int)(count * transverse / (2 * (dl + dw))) * Math.PI * d * d / 4 * c.N("bond_wire.length_" + axis) / (span * transverse * d);
            }

            c.Derived(MaterialLibrary.Mix(prefix + "-bondwire-" + axis, wire, mold, fraction, template != "chip_array" && c.T("bond_wire.modeling") == "isotropicCuboid" ? "xyz" : axis + "z"));
        }

        if (template is not ("sop" or "pqfp"))
            return;
        var metal = c.Component("group-lead-frame", "leadframe-c194");
        foreach (string location in new[]
        {
            "inner",
            "outer"
        }

        )
            foreach (string axis in template == "pqfp" ? new[]
            {
                "x",
                "y"
            }

            : new[]
            {
                ""
            }

            )
            {
                double f = location == "inner" && c.B("leads.custom_coverage") ? c.N("leads.coverage") / 100 : c.N("leads.width") / c.N("leads.pitch");
                var matrix = location == "inner" ? mold : c.M("static-air");
                c.Derived(MaterialLibrary.Mix(template + "-leadframe-" + location + (axis == "" ? "" : "-" + axis), metal, matrix, f, axis != "" && c.T("leads.modeling") == "orthotropicCuboid" ? axis + "z" : "xyz"));
            }

        c.Derived(MaterialLibrary.Mix(template + "-die-flag", c.Component(template == "sop" ? "group-die-flag" : "group-lead-frame", "leadframe-c194"), mold, c.N("flag.coverage") / 100, "xyz", false));
        if (template == "pqfp")
        {
            double a = (c.N("body.length") - c.N("flag.length")) / 2, b = (c.N("body.width") - c.N("flag.width")) / 2;
            if (a <= 0 || b <= 0)
                throw new ArgumentException("连接筋跨度必须大于零。");
            double factor = Math.Sqrt(a * a + b * b) * (1 / a + 1 / b);
            c.Derived(metal with { Id = "pqfp-tie-bar", Conductivity = new(metal.Conductivity.X / factor, metal.Conductivity.Y / factor, mold.Conductivity.Z) });
        }
    }

    public static void Qfn(BuildContext c, double dieTop, double leadTop)
    {
        double d = c.N("bond_wire.diameter");
        int steps = c.I("bond_wire.steps");
        var wire = c.Component("group-bond-wires", "gold");
        var matrix = c.Component("group-encapsulant", "eme-7730lf");
        foreach (var(axis, transverseAxis)in new[]
        {
            ("x", "y"),
            ("y", "x")
        }

        )
        {
            int count = (int)c.N("leads.count_" + transverseAxis, 0);
            if (count == 0)
                continue;
            double die = c.N(axis == "x" ? "die.length" : "die.width"), dt = c.N(axis == "x" ? "die.width" : "die.length");
            double extent = (count - 1) * c.N("leads.pitch_" + transverseAxis) + c.N("leads.width");
            double end = c.N(axis == "x" ? "package.length" : "package.width") / 2 - c.N("leads.length") - c.N("leads.etch"), span = end - die / 2;
            if (span <= 0)
                throw new ArgumentException("QFN 键合线焊盘必须位于芯片外。");
            void Pair(string id, double start, double radial, double transverse, double z, double height, string mat)
            {
                foreach (int sign in new[]
                {
                    -1,
                    1
                }

                )
                {
                    double p = sign == 1 ? start : -start - radial;
                    c.Add($"{id}-{sign}", "bond_wire", axis == "x" ? p : -transverse / 2, axis == "x" ? -transverse / 2 : p, z, axis == "x" ? radial : transverse, axis == "x" ? transverse : radial, height, mat, "bond-wires", derived: true);
                }
            }

            for (int i = 0; i < steps; i++)
            {
                double transverse = steps == 1 ? extent : dt + i * (extent - dt) / (steps - 1);
                string id = $"qfn-bondwire-{axis}" + (i < steps - 1 ? $"-{i}" : "");
                double fraction = count * Math.PI * d * c.N("bond_wire.length_" + axis) / (4 * span * transverse);
                c.Derived(MaterialLibrary.Mix(id, wire, matrix, fraction, axis + "z"));
                Pair(id, die / 2 + i * span / steps, span / steps, transverse, dieTop - d, d, id);
            }

            if (dieTop > leadTop)
                Pair($"qfn-bondwire-{axis}-v", end, d, extent, leadTop, dieTop - leadTop, $"qfn-bondwire-{axis}");
        }
    }
}
