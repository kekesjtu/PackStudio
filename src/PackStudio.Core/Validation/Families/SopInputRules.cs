namespace PackStudio.Core;

internal static class SopInputRules
{
    public static void Validate(InputChecks c)
    {
        LeadframeInputRules.Validate(c, "flag.thickness", "leads.gap", "leads.gap");
        c.Check(c.N("leads.total") % 2 != 0, "input.sop.leads", "SOP 引脚数量必须为偶数。", "leads.total");
    }
}
