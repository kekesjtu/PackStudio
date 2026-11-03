namespace PackStudio.Core;
public static class Covers
{
    public static void Build(BuildContext c, double dl, double dw, double substrateTop, double dieTop)
    {
        switch (c.T("cover.type"))
        {
            case "encapsulant":
                c.Center("encapsulant", "encapsulant", c.N("cover.length"), c.N("cover.width"), c.B("cover.flush") ? dieTop - substrateTop : c.N("cover.thickness"), substrateTop, "epoxy-mold", "encapsulant");
                break;
            case "plate":
                c.Center("thermal-plate", "heat_slug", c.N("plate.length"), c.N("plate.width"), c.N("plate.thickness"), dieTop, "aluminum", "plate");
                c.Center("plate-die-attach", "thermal_interface", dl, dw, c.N("plate.die_attach"), dieTop, "flip-cap-grease", "plate-die-attach");
                break;
            case "lid":
                double l = c.N("lid.length"), w = c.N("lid.width"), il = l - 2 * c.N("lid.base_thickness"), iw = w - 2 * c.N("lid.base_thickness");
                bool stiff = c.B("stiffener.enabled");
                if (stiff)
                {
                    l = c.N("stiffener.length");
                    w = c.N("stiffener.width");
                    il = c.N("stiffener.cavity_length");
                    iw = c.N("stiffener.cavity_width");
                }

                c.Center("lid", "lid", c.N("lid.length"), c.N("lid.width"), c.N("lid.thickness"), dieTop, "aluminum", "lid");
                c.Ring(stiff ? "stiffener" : "lid-wall", "lid", l, w, il, iw, substrateTop, dieTop - substrateTop, "aluminum", stiff ? "stiffener" : "lid");
                c.Ring("lid-adhesive", "die_attach", l, w, il, iw, stiff ? dieTop : substrateTop, c.N("lid.adhesive"), "stiffener-adhesive", "lid-adhesive");
                c.Center("lid-die-attach", "thermal_interface", dl, dw, c.N("lid.die_attach"), dieTop, "flip-cap-grease", "lid-die-attach");
                if (stiff)
                    c.Ring("stiffener-adhesive", "die_attach", l, w, il, iw, substrateTop, c.N("stiffener.adhesive"), "stiffener-adhesive", "stiffener-adhesive");
                break;
        }
    }

    public static void Slug(BuildContext c, double substrateTop, bool wirebond)
    {
        if (!c.B("slug.enabled") || !wirebond && c.T("cover.type") != "encapsulant")
            return;
        double l = c.N("slug.length"), w = c.N("slug.width"), h = c.N("slug.thickness"), side = Math.Sqrt(Math.PI) * c.N("slug.diameter") / 2, clearance = c.N("slug.clearance");
        double encap = !wirebond && c.B("cover.flush") ? c.N("bumps.height") + c.N("die.thickness") : c.N(wirebond ? "encapsulant.thickness" : "cover.thickness");
        double supportTop = substrateTop + (wirebond ? c.N("solder_mask.thickness") : 0);
        double top = substrateTop + encap, hz = top - h - c.N("slug.offset"), fz = supportTop + clearance;
        c.Center("slug-top", "heat_slug", side, side, h, top - h, "aluminum", "slug");
        c.Ring("slug-h", "heat_slug", l, w, side, side, hz, h, "aluminum", "slug");
        c.Ring("slug-v", "heat_slug", l, w, l - 2 * h, w - 2 * h, fz, hz - fz, "aluminum", "slug");
        double tx = (c.N("slug.foot_length") - l) / 2, ty = (c.N("slug.foot_width") - w) / 2;
        foreach (var(name, sx, sy, x, y)in new[]
        {
            ("right", tx, w, (l + tx) / 2, 0.0),
            ("left", tx, w, -(l + tx) / 2, 0.0),
            ("upper", l, ty, 0.0, (w + ty) / 2),
            ("lower", l, ty, 0.0, -(w + ty) / 2)
        }

        )
        {
            c.Center("slug-foot-" + name, "heat_slug", sx, sy, h, fz, "aluminum", "slug", cx: x, cy: y);
            if (c.B("slug.adhesive_enabled"))
                c.Center("slug-adhesive-" + name, "die_attach", sx + (name is "left" or "right" ? h : 0), sy + (name is "upper" or "lower" ? h : 0), clearance, fz - clearance, "stiffener-adhesive", "slug-adhesive", cx: x + (name == "left" ? h / 2 : name == "right" ? -h / 2 : 0), cy: y + (name == "lower" ? h / 2 : name == "upper" ? -h / 2 : 0));
        }
    }
}
