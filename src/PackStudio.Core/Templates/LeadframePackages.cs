namespace PackStudio.Core;
public static class LeadframePackages
{
    public static void Build(BuildContext c)
    {
        bool sop = c.Template.Info.Id == "sop";
        string prefix = sop ? "sop" : "pqfp";
        double bl = c.N("body.length"), bw = c.N("body.width"), pl = c.N("package.length", bl), pw = c.N("package.width"), s = c.N("package.standoff"), h = c.N("leads.thickness");
        double fl = c.N("flag.length"), fw = c.N("flag.width"), fh = sop ? c.N("flag.thickness") : h;
        double dl = c.N("die.length"), dw = c.N("die.width"), dh = c.N("die.thickness"), attach = c.N("die.attach");
        double z = s + c.N("leads.height"), fz = z - c.N("flag.downset"), az = fz + fh, dz = az + attach, top = dz + dh;
        if (bl > pl || bw > pw || Math.Max(fl, dl) > bl || Math.Max(fw, dw) > bw || top > s + c.N("body.thickness"))
            throw new ArgumentException("芯片、承载台和塑封尺寸不兼容。");
        if (sop && c.I("leads.total") % 2 != 0)
            throw new ArgumentException("SOP 引脚总数必须为偶数。");
        c.Center("encapsulant", "encapsulant", bl, bw, c.N("body.thickness"), s, "epoxy-mold", "encapsulant");
        c.Center("die", "die", dl, dw, dh, dz, "silicon", "die");
        c.Center("die-attach", "die_attach", dl, dw, attach, az, "dieattach-84-1lmis", "die-attach");
        c.Center("die-flag", "lead_frame", fl, fw, fh, fz, prefix + "-die-flag", "die-flag", derived: true);
        double gx = c.N(sop ? "leads.gap" : "leads.gap_x"), gy = c.N(sop ? "leads.gap" : "leads.gap_y");
        double endX = fl / 2 + gx, endY = fw / 2 + gy, leadTop = z + h, d = c.N("bond_wire.diameter");
        bool above = sop ? top > leadTop : top >= leadTop;
        Wires.FourSides(c, dl, dw, endX, endY, above ? endX : dl / 2 - d, above ? endY : dw / 2 - d, Math.Max(top, leadTop) - d, Math.Min(top, leadTop), sop ? Math.Abs(ParameterRules.SopWireHeight(c.Values)) : Math.Abs(top - leadTop), prefix + "-bondwire-x", prefix + "-bondwire-y", d / 4);
        double pitch = c.N("leads.pitch"), lw = c.N("leads.width"), foot = c.N("leads.foot_length");
        void Lead(string id, double x, double y, double zz, double sx, double sy, double sz, string mat) => c.Add(id, "lead_frame", x, y, zz, sx, sy, sz, mat, "lead-frame", derived: true);
        if (sop)
        {
            double span = (c.I("leads.total") / 2 - 1) * pitch + lw, ox = span / 2, ix = fl / 2 + gx, iy = fw / 2 + gy, by = bw / 2, oy = pw / 2 - foot + h, bend = pw / 2 - foot;
            foreach (int sign in new[]
            {
                -1,
                1
            }

            )
            {
                string side = sign == 1 ? "upper" : "lower", xs = sign == 1 ? "right" : "left";
                Lead("sop-inner-" + xs, sign == 1 ? ix : -ox, -iy, z, ox - ix, 2 * iy, h, "sop-leadframe-inner");
                Lead("sop-inner-" + side, -ox, sign == 1 ? iy : -by, z, span, by - iy, h, "sop-leadframe-inner");
                Lead("sop-outer-" + side, -ox, sign == 1 ? by : -oy, z, span, oy - by, h, "sop-leadframe-outer");
                Lead("sop-bend-" + side, -ox, sign == 1 ? bend : -bend - h, h, span, h, z - h, "sop-leadframe-outer");
                Lead("sop-foot-" + side, -ox, sign == 1 ? bend : -pw / 2, 0, span, foot, h, "sop-leadframe-outer");
                c.Add("tie-bar-" + xs, "lead_frame", sign == 1 ? fl / 2 : -bl / 2, -c.N("tie_bar.width") / 2, fz, (bl - fl) / 2, c.N("tie_bar.width"), fh, "sop-die-flag", "tie-bars", derived: true);
            }
        }
        else
        {
            double sx = (c.I("leads.count_x") - 1) * pitch + lw, sy = (c.I("leads.count_y") - 1) * pitch + lw, footWidth = foot - h;
            if (footWidth <= 0)
                throw new ArgumentException("PQFP 引脚脚长必须大于引脚厚度。");
            void Sides(string id, double ix, double iy, double ox, double oy, string kind)
            {
                Lead(id + "-right", ix, -sy / 2, z, ox - ix, sy, h, $"pqfp-leadframe-{kind}-x");
                Lead(id + "-left", -ox, -sy / 2, z, ox - ix, sy, h, $"pqfp-leadframe-{kind}-x");
                Lead(id + "-upper", -sx / 2, iy, z, sx, oy - iy, h, $"pqfp-leadframe-{kind}-y");
                Lead(id + "-lower", -sx / 2, -oy, z, sx, oy - iy, h, $"pqfp-leadframe-{kind}-y");
            }

            Sides("pqfp-inner", endX, endY, bl / 2, bw / 2, "inner");
            Sides("pqfp-outer", bl / 2, bw / 2, pl / 2 - footWidth, pw / 2 - footWidth, "outer");
            foreach (int sign in new[]
            {
                -1,
                1
            }

            )
            {
                Lead("pqfp-" + (sign == 1 ? "right" : "left"), sign == 1 ? pl / 2 - foot : -pl / 2 + foot - h, -sy / 2, 0, h, sy, z, "pqfp-leadframe-outer-x");
                Lead("pqfp-" + (sign == 1 ? "upper" : "lower"), -sx / 2, sign == 1 ? pw / 2 - foot : -pw / 2 + foot - h, 0, sx, h, z, "pqfp-leadframe-outer-y");
                Lead("pqfp-foot-" + (sign == 1 ? "right" : "left"), sign == 1 ? pl / 2 - footWidth : -pl / 2, -sy / 2, 0, footWidth, sy, h, "pqfp-leadframe-outer-x");
                Lead("pqfp-foot-" + (sign == 1 ? "upper" : "lower"), -sx / 2, sign == 1 ? pw / 2 - footWidth : -pw / 2, 0, sx, footWidth, h, "pqfp-leadframe-outer-y");
            }

            double bar = c.N("tie_bar.width");
            foreach (int xs in new[]
            {
                -1,
                1
            }

            )
                foreach (int ys in new[]
                {
                    -1,
                    1
                }

                )
                {
                    c.Add($"tie-bar-x-{xs}-{ys}", "lead_frame", xs == 1 ? fl / 2 : -bl / 2, ys == 1 ? fw / 2 - bar : -fw / 2, fz, (bl - fl) / 2, bar, h, "pqfp-tie-bar", "tie-bars", derived: true);
                    c.Add($"tie-bar-y-{xs}-{ys}", "lead_frame", xs == 1 ? fl / 2 - bar : -fl / 2, ys == 1 ? fw / 2 : -bw / 2, fz, bar, (bw - fw) / 2, h, "pqfp-tie-bar", "tie-bars", derived: true);
                }
        }

        if (c.B("thermal_land.enabled"))
        {
            if (s <= 0)
                throw new ArgumentException("散热焊盘焊料需要正的离地高度。");
            double th = c.N("thermal_land.thickness");
            c.Center("thermal-land", "exposed_pad", fl, fw, th, -th, "leadframe-c194", "thermal-land");
            c.Center("thermal-solder", "solder", fl, fw, s, 0, "solder-sn63", "thermal-solder");
        }

        Wires.Coupled(c);
    }
}
