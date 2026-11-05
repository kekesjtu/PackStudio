namespace PackStudio.Core;

internal static class PqfpInputRules
{
    public static void Validate(InputChecks c)
    {
        c.Check(c.N("leads.foot_length") <= c.N("leads.thickness"), "input.pqfp.foot", "PQFP 引脚脚长必须大于引脚厚度。", "leads.foot_length", "leads.thickness");
        LeadframeInputRules.Validate(c, "leads.thickness", "leads.gap_x", "leads.gap_y");
    }
}
