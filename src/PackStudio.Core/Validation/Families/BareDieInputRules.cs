namespace PackStudio.Core;

internal static class BareDieInputRules
{
    public static void Validate(InputChecks c)
    {
        if (c.B("bumps.enabled")) BumpInputRules.Validate(c);
    }
}
