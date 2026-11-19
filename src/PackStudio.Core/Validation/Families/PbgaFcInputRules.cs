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
        ViaInputRules.Validate(c, board: "substrate");
        MetalLayerInputRules.Validate(c);
        c.Fits("die.length", "substrate.length"); c.Fits("die.width", "substrate.width");
        var stack = BuildUpStack.Read(c.B, c.N);
        c.Check(c.B("vias.enabled") ? stack.CoreThickness <= 1e-10 : stack.CoreThickness < -1e-10,
            "input.substrate.core", c.B("vias.enabled") ? "通孔核心厚度必须大于零。" : "上下增层总厚度不能超过基板厚度。",
            "upper.thickness", "lower.thickness", "substrate.thickness");
        foreach (string region in new[] { "upper", "lower" })
        {
            if (!c.B(region + ".enabled")) continue;
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
