namespace PackStudio.Core;

internal static class PbgaFcInputRules
{
    public static void Validate(InputChecks c)
    {
        SolderBallInputRules.Validate(c);
        c.Check(c.T("bga.representation") == "isotropic", "input.bga.representation", "当前封装不支持所选焊球建模方式。", "bga.representation");
        BumpInputRules.Validate(c);
        CoverInputRules.Validate(c);
        ViaInputRules.Validate(c);
        MetalLayerInputRules.Validate(c);
        c.Fits("die.length", "substrate.length"); c.Fits("die.width", "substrate.width");
        c.Check((c.B("upper.enabled") ? c.N("upper.thickness") : 0) + (c.B("lower.enabled") ? c.N("lower.thickness") : 0) >= c.N("substrate.thickness") && c.B("vias.enabled"),
            "input.substrate.core", "通孔核心厚度必须大于零。", "upper.thickness", "lower.thickness", "substrate.thickness");
    }
}
