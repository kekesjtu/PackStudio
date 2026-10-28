namespace PackStudio.Core;
public static class Qfn
{
    public static void Build(BuildContext c)
    {
        double l = c.N("package.length"), w = c.N("package.width"), s = c.N("package.standoff"), h = c.N("leads.thickness"), eh = c.N("leads.exposed_thickness");
        double pl = c.N("pad.length"), pw = c.N("pad.width"), el = c.N("pad.exposed_length"), ew = c.N("pad.exposed_width");
        double dl = c.N("die.length"), dw = c.N("die.width"), attach = c.N("die.attach"), dh = c.N("die.thickness");
        int nx = c.I("leads.count_x"), ny = (int)c.N("leads.count_y", 0);
        double px = c.N("leads.pitch_x"), py = ny > 0 ? c.N("leads.pitch_y") : 0;
        if (nx + ny == 0 || Math.Max(dl, pl) > l || Math.Max(dw, pw) > w || eh >= h || (nx - 1) * px + c.N("leads.width") > l || ny > 0 && (ny - 1) * py + c.N("leads.width") > w)
            throw new ArgumentException("QFN 芯片、焊盘或引脚尺寸不兼容。");
        c.Center("encapsulant", "encapsulant", l, w, c.N("encapsulant.thickness"), s, "eme-7730lf", "encapsulant");
        c.Center("dap-upper", "exposed_pad", pl, pw, h - eh, s + eh, "leadframe-c194", "exposed-pad");
        c.Center("dap-exposed", "exposed_pad", el, ew, eh, s, "leadframe-c194", "exposed-pad");
        c.Center("center-solder", "solder", el, ew, s, 0, "solder-sn63", "solder");
        c.Center("die-attach", "die_attach", dl, dw, attach, s + h, "dieattach-2600bt", "die-attach");
        c.Center("die", "die", dl, dw, dh, s + h + attach, "silicon", "die");
        Wires.Qfn(c, s + h + attach + dh, s + h);
        Leads(c, l, w, nx, ny, px, py, s, h, eh);
        if (c.B("thermal_land.enabled"))
        {
            double th = c.N("thermal_land.thickness");
            c.Center("thermal-land", "exposed_pad", el, ew, th, -th, "leadframe-c194", "thermal-land");
        }

        Vias.Qfn(c);
    }

    static void Leads(BuildContext c, double l, double w, int nx, int ny, double px, double py, double s, double h, double eh)
    {
        int first = c.Model.Blocks.Count;
        double width = c.N("leads.width"), length = c.N("leads.length"), etch = c.N("leads.etch");
        foreach (var(axis, count, pitch, body)in new[]
        {
            ("y", nx, px, w),
            ("x", ny, py, l)
        }

        )
            for (int i = 0; i < count; i++)
                foreach (int sign in new[]
                {
                    -1,
                    1
                }

                )
                {
                    double transverse = (i - (count - 1) / 2.0) * pitch - width / 2, radial = sign == 1 ? body / 2 - length : -body / 2, upper = sign == 1 ? radial - etch : radial;
                    string side = axis == "x" ? (sign == 1 ? "right" : "left") : (sign == 1 ? "upper" : "lower");
                    void Add(string level, double start, double len, double z, double height, string type, string mat, string group) => c.Add($"{level}-{side}-{i + 1}", type, axis == "x" ? start : transverse, axis == "x" ? transverse : start, z, axis == "x" ? len : width, axis == "x" ? width : len, height, mat, group);
                    Add("solder", radial, length, 0, s, "solder", "solder-sn63", "solder");
                    Add("lead-lower", radial, length, s, eh, "lead_frame", "leadframe-c194", "lead-frame");
                    Add("lead-upper", upper, length + etch, s + eh, h - eh, "lead_frame", "leadframe-c194", "lead-frame");
                }

        if (c.T("leads.modeling") == "discreteLeads")
            return;
        var drafts = c.Model.Blocks.Skip(first).ToList();
        c.Model.Blocks.RemoveRange(first, drafts.Count);
        foreach (var(axis, count, pitch, sides)in new[]
        {
            ("x", ny, py, new[] { "left", "right" }),
            ("y", nx, px, new[] { "lower", "upper" })
        }

        )
        {
            if (count == 0)
                continue;
            double f = count * width / ((count - 1) * pitch + width);
            foreach (string kind in new[]
            {
                "lead",
                "solder"
            }

            )
            {
                string group = kind == "lead" ? "group-lead-frame" : "group-solder", id = $"qfn-{kind}-{axis}";
                c.Derived(MaterialLibrary.Mix(id, c.Component(group, kind == "lead" ? "leadframe-c194" : "solder-sn63"), kind == "lead" ? c.Component("group-encapsulant", "eme-7730lf") : c.M("static-air"), f, axis + "z"));
                foreach (string level in kind == "lead" ? new[]
                {
                    "lead-lower",
                    "lead-upper"
                }

                : new[]
                {
                    "solder"
                }

                )
                    foreach (string side in sides)
                    {
                        var selected = drafts.Where(d => d.Id.StartsWith($"{level}-{side}-", StringComparison.Ordinal)).ToList();
                        var low = new Vector(selected.Min(d => d.Origin.X), selected.Min(d => d.Origin.Y), selected.Min(d => d.Origin.Z));
                        var high = new Vector(selected.Max(d => d.Maximum.X), selected.Max(d => d.Maximum.Y), selected.Max(d => d.Maximum.Z));
                        c.Add($"{level}-{side}", selected[0].StructureType, low.X, low.Y, low.Z, high.X - low.X, high.Y - low.Y, high.Z - low.Z, id, group, derived: true);
                    }
            }
        }
    }
}
