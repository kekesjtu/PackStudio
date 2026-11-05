namespace PackStudio.Core;

internal static class ChipArrayInputRules
{
    public static void Validate(InputChecks c)
    {
        SolderBallInputRules.Validate(c);
        c.Check(c.T("bga.representation") != "discrete", "input.bga.representation", "当前封装不支持所选焊球建模方式。", "bga.representation");
        ViaInputRules.Validate(c, c.B("vias.filled"));
        MetalLayerInputRules.Validate(c, checkSurfaces: true);
        c.Fits("die.length", "package.length");
        c.Fits("die.width", "package.width");
        if (c.B("bond_wire.include")) WireInputRules.ValidateExtent(c, accountForDiameter: true);
    }
}
