namespace PackStudio.Core;

internal static class PbgaWbInputRules
{
    public static void Validate(InputChecks c)
    {
        SolderBallInputRules.Validate(c, "package");
        ViaInputRules.Validate(c);
        MetalLayerInputRules.Validate(c, checkSurfaces: true);
        SlugInputRules.Validate(c, wirebond: true);
        c.Fits("die.length", "encapsulant.length");
        c.Fits("die.width", "encapsulant.width");
        c.Fits("encapsulant.length", "package.length");
        c.Fits("encapsulant.width", "package.width");
        c.Fits("flag.length", "encapsulant.length");
        c.Fits("flag.width", "encapsulant.width");
        c.Fits("bond_wire.extent_length", "encapsulant.length");
        c.Fits("bond_wire.extent_width", "encapsulant.width");
        double stack = c.N("solder_mask.thickness") + c.N("die.attach") + c.N("die.thickness");
        c.Check(stack > c.N("encapsulant.thickness") + 1e-10, "input.encapsulant.stack",
            "塑封厚度必须覆盖阻焊层、粘接层和芯片。", "encapsulant.thickness", "solder_mask.thickness", "die.attach", "die.thickness");
        if (c.B("spreader.enabled"))
        {
            c.Fits("spreader.length", "package.length");
            c.Fits("spreader.width", "package.width");
            c.Fits("spreader.thickness", "substrate.thickness");
            c.Ring("package.length", "package.width", "spreader.hole_length", "spreader.hole_width");
        }
        WireInputRules.ValidateExtent(c);
        WireInputRules.Equivalent(c, c.N("bond_wire.total"), "bond_wire.total");
        c.Check(stack - c.N("bond_wire.diameter") <= 0,
            "input.wire.height", "键合线纵向高度必须为正。", "solder_mask.thickness", "die.attach", "die.thickness", "bond_wire.diameter");
        c.Check(c.N("bond_wire.extent_length") + 0.1 >= c.N("package.length") || c.N("bond_wire.extent_width") + 0.1 >= c.N("package.width"),
            "input.wire.mask", "阻焊层开口必须位于封装内。", "bond_wire.extent_length", "bond_wire.extent_width", "package.length", "package.width");
    }
}
