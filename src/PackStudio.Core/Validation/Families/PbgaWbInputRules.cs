namespace PackStudio.Core;

internal static class PbgaWbInputRules
{
    public static void Validate(InputChecks c)
    {
        SolderBallInputRules.Validate(c);
        ViaInputRules.Validate(c);
        MetalLayerInputRules.Validate(c, checkSurfaces: true);
        c.Fits("die.length", "encapsulant.length");
        c.Fits("die.width", "encapsulant.width");
        c.Fits("encapsulant.length", "package.length");
        c.Fits("encapsulant.width", "package.width");
        c.Fits("flag.length", "encapsulant.length");
        c.Fits("flag.width", "encapsulant.width");
        if (c.B("spreader.enabled"))
        {
            c.Fits("spreader.length", "package.length");
            c.Fits("spreader.width", "package.width");
            c.Fits("spreader.thickness", "substrate.thickness");
            c.Ring("package.length", "package.width", "spreader.hole_length", "spreader.hole_width");
        }
        WireInputRules.ValidateExtent(c);
    }
}
