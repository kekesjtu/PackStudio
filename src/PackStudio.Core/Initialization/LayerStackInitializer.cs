using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static class LayerStackInitializer
{
    public static void Apply(PackageDefinition definition, JObject values, JObject? overrides = null)
    {
        if (definition.Info.Id is not ("chip_array" or "pbga_wb")) return;
        const string tableKey = "metal.layers";
        if (overrides?.Properties().Any(p => p.Name == tableKey || p.Name.StartsWith(tableKey + "/", StringComparison.Ordinal)) == true)
            return;
        if (values[tableKey] is JArray { Count: >= 2 } surfaceRows && surfaceRows.All(r => r is JObject))
        {
            surfaceRows[0]!["thickness"] = Value(values, "trace.top_thickness");
            surfaceRows[surfaceRows.Count - 1]!["thickness"] = Value(values, "trace.bottom_thickness");
        }
        if (values["substrate.layers"] is not { Type: JTokenType.String } layers || layers.Value<string>() != "4-Layer") return;
        if (values[tableKey] is not JArray { Count: 4 } rows || rows.Any(r => r is not JObject)) return;
        double? height = Number(values, "substrate.thickness"), top = Number(values, "trace.top_thickness"),
            bottom = Number(values, "trace.bottom_thickness"), solid = Number(values, "trace.solid_thickness");
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
