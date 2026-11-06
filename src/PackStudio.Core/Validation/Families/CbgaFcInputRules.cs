namespace PackStudio.Core;

internal static class CbgaFcInputRules
{
    public static void Validate(InputChecks c)
    {
        SolderBallInputRules.Validate(c, "substrate");
        c.Check(c.T("bga.representation") == "isotropic", "input.bga.representation", "当前封装不支持所选焊球建模方式。", "bga.representation");
        BumpInputRules.Validate(c);
        CoverInputRules.Validate(c);
        SlugInputRules.Validate(c, wirebond: false);
        c.Fits("die.length", "substrate.length"); c.Fits("die.width", "substrate.width");
    }
}
