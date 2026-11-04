using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static class LayerStackInitializer
{
    public static void Apply(PackageDefinition definition, JObject values, JObject? overrides = null)
    {
        string tableKey = definition.Data["surface_layers"]?["table"].Text() ?? "";
        if (tableKey.Length > 0 && overrides?.Properties().Any(p => p.Name == tableKey || p.Name.StartsWith(tableKey + "/", StringComparison.Ordinal)) == true)
            return;
        if (definition.Data["surface_layers"] is JObject surfaces && values[surfaces["table"].Text()] is JArray { Count: >= 2 } surfaceRows && surfaceRows.All(r => r is JObject))
        {
            surfaceRows[0]!["thickness"] = Value(values, surfaces["top_thickness"].Text());
            surfaceRows[surfaceRows.Count - 1]!["thickness"] = Value(values, surfaces["bottom_thickness"].Text());
        }
        if (definition.Data["layer_stack"] is not JObject stack || !JsonData.Matches(stack["when"] as JObject, values)) return;
        if (values[stack["table"].Text()] is not JArray { Count: 4 } rows || rows.Any(r => r is not JObject)) return;
        double? height = Number(values, stack["height"].Text()), top = Number(values, stack["top_thickness"].Text()),
            bottom = Number(values, stack["bottom_thickness"].Text()), solid = Number(values, stack["inner_thickness"].Text());
        double? gap = (height - top - bottom - 2 * solid) / 3;
        rows[0]!["thickness"] = Token(top);
        rows[1]!["depth"] = Token(top + gap);
        rows[2]!["depth"] = Token(top + 2 * gap);
        rows[1]!["thickness"] = Token(solid);
        rows[2]!["thickness"] = Token(solid);
        rows[3]!["depth"] = Token(height - bottom);
        rows[3]!["thickness"] = Token(bottom);
    }

    static JToken Value(JObject values, string key) => values[key]?.DeepClone() ?? JValue.CreateNull();
    static double? Number(JObject values, string key) => values[key]?.Type is JTokenType.Integer or JTokenType.Float &&
        double.IsFinite(values[key]!.Number()) ? values[key]!.Number() : null;
    static JToken Token(double? value) => value is double number && double.IsFinite(number) ? new JValue(number) : JValue.CreateNull();
}
