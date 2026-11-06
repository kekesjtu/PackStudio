namespace PackStudio.Core;

internal static class PbgaFcInputRules
{
    public static void Validate(InputChecks c)
    {
        SolderBallInputRules.Validate(c, "substrate");
        c.Check(c.T("bga.representation") == "isotropic", "input.bga.representation", "当前封装不支持所选焊球建模方式。", "bga.representation");
        BumpInputRules.Validate(c);
        CoverInputRules.Validate(c);
        SlugInputRules.Validate(c, wirebond: false);
        ViaInputRules.Validate(c);
        MetalLayerInputRules.Validate(c);
        c.Fits("die.length", "substrate.length"); c.Fits("die.width", "substrate.width");
        c.Check((c.B("upper.enabled") ? c.N("upper.thickness") : 0) + (c.B("lower.enabled") ? c.N("lower.thickness") : 0) >= c.N("substrate.thickness") && c.B("vias.enabled"),
            "input.substrate.core", "通孔核心厚度必须大于零。", "upper.thickness", "lower.thickness", "substrate.thickness");
        foreach (string region in new[] { "upper", "lower" })
        {
            if (!c.B(region + ".enabled")) continue;
            MetalLayerInputRules.ValidateBuildUp(c, region);
            double diameter = c.N(region + ".diameter"), plating = c.N(region + ".plating");
            if (!c.B(region + ".filled"))
                c.Check(diameter <= 0 || !double.IsFinite(plating) || plating <= 0 || plating > diameter / 2,
                    "input.microvia.plating", "微通孔镀层厚度不超过孔半径。", region + ".plating", region + ".diameter");
            double fraction = c.N(region + ".count") * Math.PI * diameter * diameter / (4 * c.N("die.length") * c.N("die.width"));
            c.Check(fraction > 1, "input.microvia.fraction", "微通孔等效体积分数不能超过芯片区域。",
                region + ".count", region + ".diameter", "die.length", "die.width");
        }
    }
}
