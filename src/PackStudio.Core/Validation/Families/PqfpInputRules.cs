namespace PackStudio.Core;

internal static class PqfpInputRules
{
    public static void Validate(InputChecks c)
    {
        c.Check(c.N("leads.foot_length") <= c.N("leads.thickness"), "input.pqfp.foot", "PQFP 引脚脚长必须大于引脚厚度。", "leads.foot_length", "leads.thickness");
        LeadframeInputRules.Validate(c, "leads.thickness", "leads.gap_x", "leads.gap_y");
        WireInputRules.Equivalent(c, c.N("bond_wire.count"), "bond_wire.count");
        double count = c.N("bond_wire.count"), d = c.N("bond_wire.diameter"), dl = c.N("die.length"), dw = c.N("die.width");
        double vertical = Math.Abs(LeadframeStack.Evaluate(c.Values, false).WireHeight);
        foreach (string axis in new[] { "x", "y" })
        {
            double transverse = axis == "x" ? dw : dl, die = axis == "x" ? dl : dw, flag = c.N(axis == "x" ? "flag.length" : "flag.width");
            double span = (flag - die) / 2 + c.N("leads.gap_" + axis) + vertical;
            double fraction = (int)(count * transverse / (2 * (dl + dw))) * Math.PI * d * d / 4 * c.N("bond_wire.length_" + axis) / (span * transverse * d);
            c.Check(fraction > 1, "input.pqfp.wire", "键合线等效体积分数不能超过塑封空间。",
                ["bond_wire.count", "bond_wire.diameter", "bond_wire.length_" + axis, "die.length", "die.width", "flag." + (axis == "x" ? "length" : "width"), "leads.gap_" + axis]);
        }
    }
}
