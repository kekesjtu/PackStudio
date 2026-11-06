namespace PackStudio.Core;

public static class PqfpGenerator
{
    public static PackageGeometry Generate(BuildContext c)
    {
        double bl = c.N("body.length"), bw = c.N("body.width"), pl = c.N("package.length", bl), pw = c.N("package.width"), s = c.N("package.standoff"), h = c.N("leads.thickness");
        double fl = c.N("flag.length"), fw = c.N("flag.width"), fh = h;
        double dl = c.N("die.length"), dw = c.N("die.width"), dh = c.N("die.thickness"), attach = c.N("die.attach");
        var stack = LeadframeStack.Evaluate(c.Values, false);
        double z = stack.LeadBottom, fz = stack.FlagBottom, az = stack.AttachBottom, dz = stack.DieBottom, top = stack.DieTop;
        c.Center("encapsulant", "encapsulant", bl, bw, c.N("body.thickness"), s, "epoxy-mold", "encapsulant");
        c.Center("die", "die", dl, dw, dh, dz, "silicon", "die");
        c.Center("die-attach", "die_attach", dl, dw, attach, az, "dieattach-84-1lmis", "die-attach");
        c.Center("die-flag", "lead_frame", fl, fw, fh, fz, "pqfp-die-flag", "die-flag", derived: true);
        double gx = c.N("leads.gap_x"), gy = c.N("leads.gap_y");
        double endX = fl / 2 + gx, endY = fw / 2 + gy, leadTop = stack.LeadTop, d = c.N("bond_wire.diameter");
        bool above = stack.WireHeight >= 0;
        Wires.FourSides(c, dl, dw, endX, endY, above ? endX : dl / 2 - d, above ? endY : dw / 2 - d, Math.Max(top, leadTop) - d, Math.Min(top, leadTop), Math.Abs(stack.WireHeight), "pqfp-bondwire-x", "pqfp-bondwire-y", d / 4);
        double pitch = c.N("leads.pitch"), lw = c.N("leads.width"), foot = c.N("leads.foot_length");
        void Lead(string id, double x, double y, double zz, double sx, double sy, double sz, string mat) => c.Add(id, "lead_frame", x, y, zz, sx, sy, sz, mat, "lead-frame", derived: true);

        double sx = (c.I("leads.count_x") - 1) * pitch + lw, sy = (c.I("leads.count_y") - 1) * pitch + lw, footWidth = foot - h;
        void Sides(string id, double ix, double iy, double ox, double oy, string kind)
        {
            Lead(id + "-right", ix, -sy / 2, z, ox - ix, sy, h, $"pqfp-leadframe-{kind}-x");
            Lead(id + "-left", -ox, -sy / 2, z, ox - ix, sy, h, $"pqfp-leadframe-{kind}-x");
            Lead(id + "-upper", -sx / 2, iy, z, sx, oy - iy, h, $"pqfp-leadframe-{kind}-y");
            Lead(id + "-lower", -sx / 2, -oy, z, sx, oy - iy, h, $"pqfp-leadframe-{kind}-y");
        }

        Sides("pqfp-inner", endX, endY, bl / 2, bw / 2, "inner");
        Sides("pqfp-outer", bl / 2, bw / 2, pl / 2 - footWidth, pw / 2 - footWidth, "outer");
        foreach (int sign in new[] { -1, 1 })
        {
            Lead("pqfp-" + (sign == 1 ? "right" : "left"), sign == 1 ? pl / 2 - foot : -pl / 2 + foot - h, -sy / 2, 0, h, sy, z, "pqfp-leadframe-outer-x");
            Lead("pqfp-" + (sign == 1 ? "upper" : "lower"), -sx / 2, sign == 1 ? pw / 2 - foot : -pw / 2 + foot - h, 0, sx, h, z, "pqfp-leadframe-outer-y");
            Lead("pqfp-foot-" + (sign == 1 ? "right" : "left"), sign == 1 ? pl / 2 - footWidth : -pl / 2, -sy / 2, 0, footWidth, sy, h, "pqfp-leadframe-outer-x");
            Lead("pqfp-foot-" + (sign == 1 ? "upper" : "lower"), -sx / 2, sign == 1 ? pw / 2 - footWidth : -pw / 2, 0, sx, footWidth, h, "pqfp-leadframe-outer-y");
        }

        double bar = c.N("tie_bar.width");
        foreach (int xs in new[] { -1, 1 })
            foreach (int ys in new[] { -1, 1 })
            {
                c.Add($"tie-bar-x-{xs}-{ys}", "lead_frame", xs == 1 ? fl / 2 : -bl / 2, ys == 1 ? fw / 2 - bar : -fw / 2, fz, (bl - fl) / 2, bar, h, "pqfp-tie-bar", "tie-bars", derived: true);
                c.Add($"tie-bar-y-{xs}-{ys}", "lead_frame", xs == 1 ? fl / 2 - bar : -fl / 2, ys == 1 ? fw / 2 : -bw / 2, fz, bar, (bw - fw) / 2, h, "pqfp-tie-bar", "tie-bars", derived: true);
            }


        if (c.B("thermal_land.enabled"))
        {
            double th = c.N("thermal_land.thickness");
            c.Center("thermal-land", "exposed_pad", fl, fw, th, -th, "leadframe-c194", "thermal-land");
            c.Center("thermal-solder", "solder", fl, fw, s, 0, "solder-sn63", "thermal-solder");
        }

        EquivalentMaterials(c);
        c.DistributeDiePower();
        var outline = new Footprint(pl, pw);
        var grid = new Footprint(Math.Max(outline.Length, outline.Width), Math.Max(outline.Length, outline.Width));
        return new(outline, grid, outline, new(bl, bw), c.Blocks.Max(b => b.Maximum.Z), false);
    }

    static void EquivalentMaterials(BuildContext c)
    {
        var mold = c.Component("group-encapsulant", "epoxy-mold");
        var metal = c.Component("group-lead-frame", "leadframe-c194");
        var wire = c.Component("group-bond-wires", "gold");
        double d = c.N("bond_wire.diameter"), dl = c.N("die.length"), dw = c.N("die.width");
        int count = c.I("bond_wire.count");
        foreach (string axis in new[] { "x", "y" })
        {
            double transverse = axis == "x" ? dw : dl, die = axis == "x" ? dl : dw, flag = c.N(axis == "x" ? "flag.length" : "flag.width");
            double vertical = Math.Abs(LeadframeStack.Evaluate(c.Values, false).WireHeight);
            double span = (flag - die) / 2 + c.N("leads.gap_" + axis) + vertical;
            double fraction = (int)(count * transverse / (2 * (dl + dw))) * Math.PI * d * d / 4 * c.N("bond_wire.length_" + axis) / (span * transverse * d);
            c.Derived(MaterialMixer.Mix("pqfp-bondwire-" + axis, wire, mold, fraction, c.T("bond_wire.modeling") == "isotropicCuboid" ? "xyz" : axis + "z"));
        }
        foreach (string location in new[] { "inner", "outer" })
            foreach (string axis in new[] { "x", "y" })
            {
                double f = location == "inner" && c.B("leads.custom_coverage") ? c.N("leads.coverage") / 100 : c.N("leads.width") / c.N("leads.pitch");
                var matrix = location == "inner" ? mold : c.M("static-air");
                c.Derived(MaterialMixer.Mix("pqfp-leadframe-" + location + (axis == "" ? "" : "-" + axis), metal, matrix, f, axis != "" && c.T("leads.modeling") == "orthotropicCuboid" ? axis + "z" : "xyz"));
            }
        c.Derived(MaterialMixer.Mix("pqfp-die-flag", c.Component("group-lead-frame", "leadframe-c194"), mold, c.N("flag.coverage") / 100, "xyz", false));
        double a = (c.N("body.length") - c.N("flag.length")) / 2, b = (c.N("body.width") - c.N("flag.width")) / 2;
        double factor = Math.Sqrt(a * a + b * b) * (1 / a + 1 / b);
        c.Derived(metal with { Id = "pqfp-tie-bar", ConductType = 2, ConductivityCoefficient = null, ReferenceTemperature = null, StoredScalarConductivity = null, StoredDirectionalConductivity = null, Conductivity = new(metal.EffectiveConductivity.X / factor, metal.EffectiveConductivity.Y / factor, mold.EffectiveConductivity.Z) });
    }
}
