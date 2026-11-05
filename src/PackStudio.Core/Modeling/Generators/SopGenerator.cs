namespace PackStudio.Core;

public static class SopGenerator
{
    public static PackageGeometry Generate(BuildContext c)
    {
        double bl = c.N("body.length"), bw = c.N("body.width"), pl = c.N("package.length", bl), pw = c.N("package.width"), s = c.N("package.standoff"), h = c.N("leads.thickness");
        double fl = c.N("flag.length"), fw = c.N("flag.width"), fh = c.N("flag.thickness");
        double dl = c.N("die.length"), dw = c.N("die.width"), dh = c.N("die.thickness"), attach = c.N("die.attach");
        var stack = LeadframeStack.Evaluate(c.Values, true);
        double z = stack.LeadBottom, fz = stack.FlagBottom, az = stack.AttachBottom, dz = stack.DieBottom, top = stack.DieTop;
        c.Center("encapsulant", "encapsulant", bl, bw, c.N("body.thickness"), s, "epoxy-mold", "encapsulant");
        c.Center("die", "die", dl, dw, dh, dz, "silicon", "die");
        c.Center("die-attach", "die_attach", dl, dw, attach, az, "dieattach-84-1lmis", "die-attach");
        c.Center("die-flag", "lead_frame", fl, fw, fh, fz, "sop-die-flag", "die-flag", derived: true);
        double gx = c.N("leads.gap"), gy = c.N("leads.gap");
        double endX = fl / 2 + gx, endY = fw / 2 + gy, leadTop = stack.LeadTop, d = c.N("bond_wire.diameter");
        bool above = stack.WireHeight > 0;
        Wires.FourSides(c, dl, dw, endX, endY, above ? endX : dl / 2 - d, above ? endY : dw / 2 - d, Math.Max(top, leadTop) - d, Math.Min(top, leadTop), Math.Abs(stack.WireHeight), "sop-bondwire-x", "sop-bondwire-y", d / 4);
        double pitch = c.N("leads.pitch"), lw = c.N("leads.width"), foot = c.N("leads.foot_length");
        void Lead(string id, double x, double y, double zz, double sx, double sy, double sz, string mat) => c.Add(id, "lead_frame", x, y, zz, sx, sy, sz, mat, "lead-frame", derived: true);

        double span = (c.I("leads.total") / 2 - 1) * pitch + lw, ox = span / 2, ix = fl / 2 + gx, iy = fw / 2 + gy, by = bw / 2, oy = pw / 2 - foot + h, bend = pw / 2 - foot;
        foreach (int sign in new[] { -1, 1 })
        {
            string side = sign == 1 ? "upper" : "lower", xs = sign == 1 ? "right" : "left";
            Lead("sop-inner-" + xs, sign == 1 ? ix : -ox, -iy, z, ox - ix, 2 * iy, h, "sop-leadframe-inner");
            Lead("sop-inner-" + side, -ox, sign == 1 ? iy : -by, z, span, by - iy, h, "sop-leadframe-inner");
            Lead("sop-outer-" + side, -ox, sign == 1 ? by : -oy, z, span, oy - by, h, "sop-leadframe-outer");
            Lead("sop-bend-" + side, -ox, sign == 1 ? bend : -bend - h, h, span, h, z - h, "sop-leadframe-outer");
            Lead("sop-foot-" + side, -ox, sign == 1 ? bend : -pw / 2, 0, span, foot, h, "sop-leadframe-outer");
            c.Add("tie-bar-" + xs, "lead_frame", sign == 1 ? fl / 2 : -bl / 2, -c.N("tie_bar.width") / 2, fz, (bl - fl) / 2, c.N("tie_bar.width"), fh, "sop-die-flag", "tie-bars", derived: true);
        }

        if (c.B("thermal_land.enabled"))
        {
            double th = c.N("thermal_land.thickness");
            c.Center("thermal-land", "exposed_pad", fl, fw, th, -th, "leadframe-c194", "thermal-land");
            c.Center("thermal-solder", "solder", fl, fw, s, 0, "solder-sn63", "thermal-solder");
        }

        EquivalentMaterials(c);
        c.DistributeDiePower();
        var outline = new Footprint(bl, pw);
        var grid = new Footprint(Math.Max(outline.Length, outline.Width), Math.Max(outline.Length, outline.Width));
        return new(outline, grid, outline, new(bl, bw), c.Blocks.Max(b => b.Maximum.Z), false);
    }

    static void EquivalentMaterials(BuildContext c)
    {
        var mold = c.Component("group-encapsulant", "epoxy-mold");
        var metal = c.Component("group-lead-frame", "leadframe-c194");
        Wires.Equivalent(c, "sop", c.I("bond_wire.count"), c.T("bond_wire.modeling") == "isotropicCuboid");
        foreach (string location in new[] { "inner", "outer" })
        {
            double f = location == "inner" && c.B("leads.custom_coverage") ? c.N("leads.coverage") / 100 : c.N("leads.width") / c.N("leads.pitch");
            var matrix = location == "inner" ? mold : c.M("static-air");
            c.Derived(MaterialMixer.Mix("sop-leadframe-" + location, metal, matrix, f, "xyz"));
        }
        c.Derived(MaterialMixer.Mix("sop-die-flag", c.Component("group-die-flag", "leadframe-c194"), mold, c.N("flag.coverage") / 100, "xyz", false));
    }
}
