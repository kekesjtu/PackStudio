using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static class ParameterCalculations
{
    public static double SopWirePath(JObject values, string dimension) =>
        (Number(values, "flag." + dimension) - Number(values, "die." + dimension)) / 2
        + Number(values, "leads.gap") + Math.Abs(LeadframeStack.Evaluate(values, true).WireHeight);

    public static double Derived(string calculation, JObject values) => calculation switch
    {
        "sop_wire_path_x" => SopWirePath(values, "length"),
        "sop_wire_path_y" => SopWirePath(values, "width"),
        _ => throw new InvalidDataException($"未知派生值 {calculation}。")
    };

    static double Number(JObject values, string key) => values[key]?.Type is JTokenType.Integer or JTokenType.Float
        ? values[key]!.Number() : double.NaN;
}
