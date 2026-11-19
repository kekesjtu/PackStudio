namespace PackStudio.Core;
public static class QfnGenerator
{
    public static PackageGeometry Generate(BuildContext c)
    {
        double l = c.N("package.length"), w = c.N("package.width"), s = c.N("package.standoff"), h = c.N("leads.thickness"), eh = c.N("leads.exposed_thickness");
        double pl = c.N("pad.length"), pw = c.N("pad.width"), el = c.N("pad.exposed_length"), ew = c.N("pad.exposed_width");
        double dl = c.N("die.length"), dw = c.N("die.width"), attach = c.N("die.attach"), dh = c.N("die.thickness");
        var rows = QfnLeadLayout.Rows(key => c.N(key, double.NaN)).ToArray();
        c.Center("encapsulant", "encapsulant", l, w, c.N("encapsulant.thickness"), s, "eme-7730lf", "encapsulant");
        c.Center("dap-upper", "exposed_pad", pl, pw, h - eh, s + eh, "leadframe-c194", "exposed-pad");
        c.Center("dap-exposed", "exposed_pad", el, ew, eh, s, "leadframe-c194", "exposed-pad");
        c.Center("center-solder", "solder", el, ew, s, 0, "solder-sn63", "solder");
        c.Center("die-attach", "die_attach", dl, dw, attach, s + h, "dieattach-2600bt", "die-attach");
        c.Center("die", "die", dl, dw, dh, s + h + attach, "silicon", "die");
        BondWires(c, rows, s + h + attach + dh, s + h);
        Leads(c, rows, s, h, eh);
        if (c.B("thermal_land.enabled"))
        {
            double th = c.N("thermal_land.thickness");
            c.Center("thermal-land", "exposed_pad", el, ew, th, -th, "leadframe-c194", "thermal-land");
        }

        ThermalVias(c);
        c.DistributeDiePower();
        var outline = new Footprint(l, w);
        var grid = new Footprint(Math.Max(l, w), Math.Max(l, w));
        return new(outline, grid, outline, outline, c.Blocks.Max(b => b.Maximum.Z), false);
    }

    static void Leads(BuildContext c, QfnLeadLayout[] rows, double s, double h, double eh)
    {
        int first = c.Blocks.Count;
        double width = c.N("leads.width"), length = c.N("leads.length"), etch = c.N("leads.etch");
        foreach (var row in rows)
            for (int i = 0; i < row.Count; i++)
                foreach (int sign in new[]
                {
                    -1,
                    1
                }

                )
                {
                    string axis = row.RadialAxis;
                    double body = row.Body;
                    double transverse = (i - (row.Count - 1) / 2.0) * row.Pitch - width / 2, radial = sign == 1 ? body / 2 - length : -body / 2, upper = sign == 1 ? radial - etch : radial;
                    string side = axis == "x" ? (sign == 1 ? "right" : "left") : (sign == 1 ? "upper" : "lower");
                    void Add(string level, double start, double len, double z, double height, string type, string mat, string group) => c.Add($"{level}-{side}-{i + 1}", type, axis == "x" ? start : transverse, axis == "x" ? transverse : start, z, axis == "x" ? len : width, axis == "x" ? width : len, height, mat, group);
                    Add("solder", radial, length, 0, s, "solder", "solder-sn63", "solder");
                    Add("lead-lower", radial, length, s, eh, "lead_frame", "leadframe-c194", "lead-frame");
                    Add("lead-upper", upper, length + etch, s + eh, h - eh, "lead_frame", "leadframe-c194", "lead-frame");
                }

        if (c.T("leads.modeling") == "discreteLeads")
            return;
        var drafts = c.Blocks.Skip(first).ToList();
        c.Blocks.RemoveRange(first, drafts.Count);
        foreach (var row in rows.Reverse())
        {
            string axis = row.RadialAxis;
            string[] sides = axis == "x" ? ["left", "right"] : ["lower", "upper"];
            double f = row.Count * width / row.Extent;
            foreach (string kind in new[]
            {
                "lead",
                "solder"
            }

            )
            {
                string group = kind == "lead" ? "group-lead-frame" : "group-solder", id = $"qfn-{kind}-{axis}";
                c.Derived(MaterialMixer.Mix(id, c.Component(group, kind == "lead" ? "leadframe-c194" : "solder-sn63"), kind == "lead" ? c.Component("group-encapsulant", "eme-7730lf") : c.M("static-air"), f, axis + "z"));
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
    static void BondWires(BuildContext c, QfnLeadLayout[] rows, double dieTop, double leadTop)
    {
        double d = c.N("bond_wire.diameter");
        int steps = c.I("bond_wire.steps");
        var wire = c.Component("group-bond-wires", "gold");
        var matrix = c.Component("group-encapsulant", "eme-7730lf");
        foreach (var row in rows.Reverse())
        {
            string axis = row.RadialAxis;
            int count = row.Count;
            double die = row.Die, dt = row.TransverseDie, extent = row.Extent, end = row.End, span = row.WireSpan;
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
                c.Derived(MaterialMixer.Mix(id, wire, matrix, fraction, axis + "z"));
                Pair(id, die / 2 + i * span / steps, span / steps, transverse, dieTop - d, d, id);
            }

            if (dieTop > leadTop)
                Pair($"qfn-bondwire-{axis}-v", end, d, extent, leadTop, dieTop - leadTop, $"qfn-bondwire-{axis}");
        }
    }

    static void ThermalVias(BuildContext c)
    {
        if (!c.B("vias.enabled"))
            return;
        var matrix = c.M("static-air")with
        {
            Conductivity = new(0.32, 0.32, 0.32),
            Density = 1200,
            SpecificHeat = 880
        };
        double height = c.N("vias.length");
        Vias.Build(c, c.M("copper"), matrix, "qfn-via", -height, height);
    }
}
