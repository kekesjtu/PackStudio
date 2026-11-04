using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static class ParameterRules
{
    public static JObject Prepare(Template template, JObject source, JObject? overrides = null)
    {
        var values = (JObject)source.DeepClone();
        template.Validate(values);
        string tableKey = template.Data["surface_layers"]?["table"].Text() ?? "";
        if (tableKey.Length > 0 && overrides?.Property(tableKey) != null) return values;
        if (template.Data["surface_layers"] is JObject surfaces && values[surfaces["table"].Text()] is JArray { Count: >= 2 } surfaceRows)
        {
            surfaceRows[0]!["thickness"] = values[surfaces["top_thickness"].Text()]!.DeepClone();
            surfaceRows[surfaceRows.Count - 1]!["thickness"] = values[surfaces["bottom_thickness"].Text()]!.DeepClone();
        }
        if (template.Data["layer_stack"] is not JObject stack ||
            !JsonData.Matches(stack["when"] as JObject, values)) return values;
        double N(string key) => values[key]?.Type is JTokenType.Integer or JTokenType.Float
            ? values[key]!.Number() : throw new ArgumentException($"{key} 需要数值。");
        double solid = N(stack["inner_thickness"].Text());
        if (values[stack["table"].Text()] is not JArray { Count: 4 } rows)
            throw new ArgumentException("四层基板需要四个金属层。");
        double height = N(stack["height"].Text()), top = N(stack["top_thickness"].Text()), bottom = N(stack["bottom_thickness"].Text());
        double gap = (height - top - bottom - 2 * solid) / 3;
        if (gap < 0) throw new ArgumentException("金属层厚度超过基板厚度。");
        rows[0]!["thickness"] = top;
        rows[1]!["depth"] = top + gap;
        rows[2]!["depth"] = top + 2 * gap;
        rows[1]!["thickness"] = rows[2]!["thickness"] = solid;
        rows[3]!["depth"] = height - bottom;
        rows[3]!["thickness"] = bottom;
        return values;
    }

    public static double SopWireHeight(JObject values) => Number(values, "die.thickness") + Number(values, "die.attach")
        + Number(values, "flag.thickness") - Number(values, "leads.thickness") - Number(values, "flag.downset");

    public static double SopWirePath(JObject values, string dimension) =>
        (Number(values, "flag." + dimension) - Number(values, "die." + dimension)) / 2
        + Number(values, "leads.gap") + Math.Abs(SopWireHeight(values));

    public static double Derived(string calculation, JObject values) => calculation switch
    {
        "sop_wire_path_x" => SopWirePath(values, "length"),
        "sop_wire_path_y" => SopWirePath(values, "width"),
        _ => throw new InvalidDataException($"未知派生值 {calculation}。")
    };

    static double Number(JObject values, string key) => values[key]?.Type is JTokenType.Integer or JTokenType.Float
        ? values[key]!.Number() : double.NaN;
}
