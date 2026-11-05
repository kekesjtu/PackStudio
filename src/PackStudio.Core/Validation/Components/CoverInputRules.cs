namespace PackStudio.Core;

internal static class CoverInputRules
{
    public static void Validate(InputChecks c)
    {
        if (c.T("cover.type") == "lid")
        {
            if (c.B("stiffener.enabled")) c.Ring("stiffener.length", "stiffener.width", "stiffener.cavity_length", "stiffener.cavity_width");
            else c.Check(2 * c.N("lid.base_thickness") >= c.N("lid.length") || 2 * c.N("lid.base_thickness") >= c.N("lid.width"),
                "input.lid.wall", "盖板侧壁必须保留正的内部开口。", "lid.base_thickness", "lid.length", "lid.width");
        }
    }
}
