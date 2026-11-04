using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public static class WirebondPackages
{
    public static void Build(BuildContext c)
    {
        bool chip = c.Template.Info.Id == "chip_array";
        double l = c.N("package.length"), w = c.N("package.width"), baseZ = c.N("bga.height"), height = c.N("substrate.thickness"), top = baseZ + height;
        var rows = MetalLayers.Parse(c, "metal.layers");
        if (rows.Count < 2 || rows.Count > (chip ? 10 : 6))
            throw new ArgumentException("金属层表需要 2–6 层。");
        double topTrace = rows[0]!["thickness"].Number(), bottomTrace = rows[rows.Count - 1]!["thickness"].Number();
        rows[0]!["depth"] = 0;
        rows[rows.Count - 1]!["depth"] = height - bottomTrace;
        if (topTrace + bottomTrace >= height || rows.Any(r => r["depth"].Number() + r["thickness"].Number() > height + 1e-12))
            throw new ArgumentException("金属层必须位于基板内。");
        double mask = c.N("solder_mask.thickness"), dl = c.N("die.length"), dw = c.N("die.width"), dh = c.N("die.thickness"), attach = c.N("die.attach"), dz = top + mask + (chip ? 0 : attach);
        double ml = chip ? l : c.N("encapsulant.length"), mw = chip ? w : c.N("encapsulant.width");
        if (dl > ml || dw > mw || ml > l || mw > w)
            throw new ArgumentException("芯片、塑封和基板尺寸不兼容。");
        c.Center("encapsulant", "encapsulant", ml, mw, c.N("encapsulant.thickness"), top, "epoxy-mold", "encapsulant");
        c.Center("die", "die", dl, dw, dh, dz, "silicon", "die");
        c.Center("dielectric", "substrate", l, w, height, baseZ, "bt", "substrate");
        c.Center("die-attach", "die_attach", dl, dw, attach, chip ? dz : top + mask, chip ? "qmi-595" : "ablestik-8510aa", "die-attach");
        double extentX = c.N("bond_wire.extent_length"), extentY = c.N("bond_wire.extent_width"), d = c.N("bond_wire.diameter");
        if (!chip || c.B("bond_wire.include"))
            Wires.FourSides(c, dl, dw, extentX / 2 - (chip ? d : 0), extentY / 2 - (chip ? d : 0), extentX / 2 - d, extentY / 2 - d, dz + dh - d, top, dz + dh - top - (chip ? 0 : d), chip ? "chip-array-bondwire-x" : "wirebond-bondwire-x", chip ? "chip-array-bondwire-y" : "wirebond-bondwire-y");
        if (chip)
        {
            c.Center("solder-mask", "solder_mask", dl, dw, mask, top, "solder-mask", "solder-mask");
            ChipDetails(c, rows, l, w, baseZ, height);
        }
        else
            WirebondDetails(c, rows, l, w, baseZ, height, extentX, extentY, d);
        Wires.Coupled(c);
        SolderBalls.Build(c);
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
        double diameter = c.N("vias.diameter"), plating = c.N("vias.plating", 0), shell = c.B("vias.filled") ? 1 : 1 - Math.Pow((diameter - 2 * plating) / diameter, 2);
        var single = MaterialLibrary.Mix("chip-array-via", metal, c.M("static-air"), shell);
        bool approximate = c.T("vias.modeling") == "approximate";
        double b = approximate ? c.N("bga.diameter") : diameter;
        if (approximate)
            single = MaterialLibrary.Mix(single.Id, single, matrix, diameter * diameter / (b * b));
        c.Derived(single);
        double side = Math.Sqrt(Math.PI) * b / 2, dx = approximate ? 0 : c.N("vias.offset_x"), dy = approximate ? 0 : c.N("vias.offset_y");
        foreach (var position in SolderBalls.MainPositions(c))
            c.Center(position.Id.Replace("solder-ball", "thermal-via").Replace("solder-map", "thermal-via-map"), "via", side, side, height - tt - bt, baseZ + bt, single.Id, "vias", derived: true, cx: position.X + dx, cy: position.Y + dy);
    }

    static void WirebondDetails(BuildContext c, JArray rows, double l, double w, double baseZ, double height, double extentX, double extentY, double d)
    {
        double top = baseZ + height, tt = rows[0]!["thickness"].Number(), bt = rows[rows.Count - 1]!["thickness"].Number(), fl = c.N("flag.length"), fw = c.N("flag.width"), mask = c.N("solder_mask.thickness");
        if (fl > c.N("encapsulant.length") || fw > c.N("encapsulant.width"))
            throw new ArgumentException("承载台必须位于塑封内。");
        var metal = c.Component("group-traces", "copper");
        var matrix = c.Component("group-substrate", "bt");
        void Mix(string id, double coverage) => c.Derived(MaterialLibrary.Mix(id, metal, matrix, coverage / 100));
        Mix("wirebond-trace-top", rows[0]!["coverage"].Number());
        Mix("wirebond-trace-bottom", rows[rows.Count - 1]!["coverage"].Number());
        Mix("wirebond-die-flag", c.N("flag.coverage"));
        c.Ring("top-trace", "trace", l, w, extentX - 2 * d, extentY - 2 * d, top - tt, tt, "wirebond-trace-top", "traces", true);
        if (!c.B("spreader.enabled"))
            c.Center("bottom-trace", "trace", l, w, bt, baseZ, "wirebond-trace-bottom", "traces", derived: true);
        else
        {
            if (c.N("spreader.length") > l || c.N("spreader.width") > w || c.N("spreader.thickness") > height)
                throw new ArgumentException("背面扩散片必须位于基板内。");
            c.Ring("bottom-trace", "trace", l, w, c.N("spreader.hole_length"), c.N("spreader.hole_width"), baseZ, bt, "wirebond-trace-bottom", "traces", true);
            c.Center("backside-spreader", "heat_slug", c.N("spreader.length"), c.N("spreader.width"), c.N("spreader.thickness"), baseZ, "copper", "backside-spreader");
        }

        for (int i = 1; i < rows.Count - 1; i++)
        {
            string id = $"wirebond-trace-{i}";
            Mix(id, rows[i]["coverage"].Number());
            c.Center($"trace-{i}", "trace", l, w, rows[i]["thickness"].Number(), top - rows[i]["depth"].Number() - rows[i]["thickness"].Number(), id, "traces", derived: true);
        }

        if (c.B("vias.enabled"))
        {
            for (int i = 0; i < rows.Count; i++)
                if (rows[i]["disconnect"].Flag())
                {
                    double lx = (c.I("vias.columns") - 1) * c.N("vias.pitch") + 3 * c.N("vias.diameter"), ly = (c.I("vias.rows") - 1) * c.N("vias.pitch") + 3 * c.N("vias.diameter");
                    c.Center($"disconnect-{i}", "substrate", lx, ly, rows[i]["thickness"].Number(), top - rows[i]["depth"].Number() - rows[i]["thickness"].Number(), matrix.Id, "via-disconnect");
                }

            Vias.Build(c, metal, matrix, "wirebond-via", baseZ + bt, height - tt - bt);
        }

        c.Center("die-flag", "lead_frame", fl, fw, tt, top - tt, "wirebond-die-flag", "die-flag", derived: true);
        c.Center("solder-mask-center", "solder_mask", fl, fw, mask, top, "solder-mask", "solder-mask");
        c.Ring("solder-mask-outer", "solder_mask", l, w, extentX + 0.1, extentY + 0.1, top, mask, "solder-mask", "solder-mask");
        Covers.Slug(c, top, true);
    }
}
