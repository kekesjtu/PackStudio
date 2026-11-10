namespace PackStudio.Core;

internal static class CoverInputRules
{
    public static void Validate(InputChecks c)
    {
        if (c.T("cover.type") != "lid") return;

        bool stiff = c.B("stiffener.enabled");
        if (stiff)
        {
            c.Ring("stiffener.length", "stiffener.width", "stiffener.cavity_length", "stiffener.cavity_width");
            c.Check(c.N("die.length") > c.N("stiffener.cavity_length") || c.N("die.width") > c.N("stiffener.cavity_width"),
                "input.lid.die", "加强环开口必须容纳芯片。",
                "die.length", "die.width", "stiffener.cavity_length", "stiffener.cavity_width");
        }
        else
        {
            double walls = 2 * c.N("lid.base_thickness"), length = c.N("lid.length"), width = c.N("lid.width");
            c.Check(walls >= length || walls >= width, "input.lid.wall", "顶盖侧壁必须保留正的内部开口。",
                "lid.base_thickness", "lid.length", "lid.width");
            c.Check(walls < length && walls < width && (c.N("die.length") + walls > length || c.N("die.width") + walls > width),
                "input.lid.die", "顶盖侧壁开口必须容纳芯片。",
                "die.length", "die.width", "lid.length", "lid.width", "lid.base_thickness");
        }

        double available = c.N("bumps.height") + c.N("die.thickness") + c.N("lid.die_attach");
        double adhesives = c.N("lid.adhesive") + (stiff ? c.N("stiffener.adhesive") : 0);
        string[] heightPaths = ["bumps.height", "die.thickness", "lid.die_attach", "lid.adhesive"];
        c.Check(adhesives >= available, "input.lid.height",
            stiff ? "胶层之间必须保留正的加强环高度。" : "胶层上方必须保留正的侧壁高度。",
            stiff ? [.. heightPaths, "stiffener.adhesive"] : heightPaths);
    }
}
