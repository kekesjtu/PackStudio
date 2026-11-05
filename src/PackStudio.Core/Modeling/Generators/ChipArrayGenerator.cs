using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static class ChipArrayGenerator
{
    public static PackageGeometry Generate(BuildContext c)
    {
        double l = c.N("package.length"), w = c.N("package.width"), baseZ = c.N("bga.height"), height = c.N("substrate.thickness"), top = baseZ + height;
        var rows = MetalLayers.Parse(c, "metal.layers");
        double topTrace = rows[0]!["thickness"].Number(), bottomTrace = rows[rows.Count - 1]!["thickness"].Number();
        rows[0]!["depth"] = 0;
        rows[rows.Count - 1]!["depth"] = height - bottomTrace;
        double mask = c.N("solder_mask.thickness"), dl = c.N("die.length"), dw = c.N("die.width"), dh = c.N("die.thickness"), attach = c.N("die.attach"), dz = top + mask;
        double ml = l, mw = w;
        c.Center("encapsulant", "encapsulant", ml, mw, c.N("encapsulant.thickness"), top, "epoxy-mold", "encapsulant", exposedSurface: true);
        c.Center("die", "die", dl, dw, dh, dz, "silicon", "die");
        c.Center("dielectric", "substrate", l, w, height, baseZ, "bt", "substrate");
        c.Center("die-attach", "die_attach", dl, dw, attach, dz, "qmi-595", "die-attach");
        double extentX = c.N("bond_wire.extent_length"), extentY = c.N("bond_wire.extent_width"), d = c.N("bond_wire.diameter");
        if (c.B("bond_wire.include"))
            Wires.FourSides(c, dl, dw, extentX / 2 - d, extentY / 2 - d, extentX / 2 - d, extentY / 2 - d, dz + dh - d, top, dz + dh - top, "chip-array-bondwire-x", "chip-array-bondwire-y");
        c.Center("solder-mask", "solder_mask", dl, dw, mask, top, "solder-mask", "solder-mask");
        ChipDetails(c, rows, l, w, baseZ, height);
        int wires = c.B("bond_wire.auto_count") ? SolderBalls.WireCount(c) : c.I("bond_wire.total");
        Wires.Equivalent(c, "chip-array", wires, false);
        SolderBalls.Build(c);
        c.DistributeDiePower();
        var outline = new Footprint(l, w);
        return new(outline, outline, SolderBalls.Footprint(c), outline, c.Blocks.Max(b => b.Maximum.Z), false);
    }

    static void ChipDetails(BuildContext c, JArray rows, double l, double w, double baseZ, double height)
    {
        var metal = c.Component("group-metal", "copper");
        var matrix = c.Component("group-substrate", "bt");
        double tt = rows[0]!["thickness"].Number(), bt = rows[rows.Count - 1]!["thickness"].Number();
        MetalLayers.Append(c, rows, l, w, baseZ + height, metal, matrix);
        if (c.Values["metal.hole_length"]?.Type is JTokenType.Integer or JTokenType.Float && c.Values["metal.hole_width"]?.Type is JTokenType.Integer or JTokenType.Float)
            c.Center("trace-hole", "trace", c.N("metal.hole_length"), c.N("metal.hole_width"), tt, baseZ + height - tt, c.Component("group-trace-hole", "bt").Id, "traces", derived: true);
        if (!c.B("vias.enabled"))
            return;
        double diameter = c.N("vias.diameter"), shell = c.B("vias.filled") ? 1 : 1 - Math.Pow((diameter - 2 * c.N("vias.plating", 0)) / diameter, 2);
        var single = MaterialMixer.Mix("chip-array-via", metal, c.M("static-air"), shell);
        bool approximate = c.T("vias.modeling") == "approximate";
        double b = approximate ? c.N("bga.diameter") : diameter;
        if (approximate)
            single = MaterialMixer.Mix(single.Id, single, matrix, diameter * diameter / (b * b));
        c.Derived(single);
        double side = Math.Sqrt(Math.PI) * b / 2, dx = approximate ? 0 : c.N("vias.offset_x"), dy = approximate ? 0 : c.N("vias.offset_y");
        foreach (var position in SolderBalls.MainPositions(c))
            c.Center(position.Id.Replace("solder-ball", "thermal-via").Replace("solder-map", "thermal-via-map"), "via", side, side, height - tt - bt, baseZ + bt, single.Id, "vias", derived: true, cx: position.X + dx, cy: position.Y + dy);
    }

}
