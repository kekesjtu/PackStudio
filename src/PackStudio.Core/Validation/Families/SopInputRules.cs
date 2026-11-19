namespace PackStudio.Core;

internal static class SopInputRules
{
    public static void Validate(InputChecks c)
    {
        c.Check(OuterLeadGeometry.SopBendHeight(LeadframeStack.Evaluate(c.Values, true).LeadBottom, c.N("leads.thickness")) <= 1e-10,
            "input.sop.bend", "引脚折弯竖段必须有正高度。", "package.standoff", "leads.height", "leads.thickness");
        LeadframeInputRules.OuterLead(c, "width");
        LeadframeInputRules.Validate(c, "flag.thickness", "leads.gap", "leads.gap");
        double count = c.N("leads.total");
        c.Check(count % 2 != 0, "input.sop.leads", "SOP 引脚数量必须为偶数。", "leads.total");
        double span = (count / 2 - 1) * c.N("leads.pitch") + c.N("leads.width");
        c.Check(count % 2 == 0 && span <= c.N("flag.length") + 2 * c.N("leads.gap"),
            "input.sop.lead_span", "单排引脚跨度必须大于载片台长度与两侧间隙之和。",
            "leads.total", "leads.pitch", "leads.width", "flag.length", "leads.gap");
        WireInputRules.Equivalent(c, c.N("bond_wire.count"), "bond_wire.count");
    }
}
