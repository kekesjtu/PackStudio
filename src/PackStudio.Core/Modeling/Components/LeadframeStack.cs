using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public sealed record LeadframeStack(double LeadBottom, double LeadTop, double FlagBottom, double AttachBottom, double DieBottom, double DieTop)
{
    public double WireHeight => DieTop - LeadTop;
    public static LeadframeStack Evaluate(JObject values, bool sop)
    {
        double N(string key) => values[key]?.Type is JTokenType.Integer or JTokenType.Float ? values[key]!.Number() : double.NaN;
        double lead = N("package.standoff") + N("leads.height"), leadTop = lead + N("leads.thickness");
        double flag = lead - N("flag.downset"), attach = flag + N(sop ? "flag.thickness" : "leads.thickness"), die = attach + N("die.attach");
        return new(lead, leadTop, flag, attach, die, die + N("die.thickness"));
    }
}
