using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Cli;

internal static class ParameterHelp
{
    public static JObject Describe(JArray fields)
    {
        var result = new JObject();
        foreach (var field in fields)
        {
            var entry = new JObject
            {
                ["label"] = field["label"]?.DeepClone(),
                ["des_symbol"] = field["des_symbol"]?.DeepClone()
            };
            if (field["options"] is JArray options)
                entry["options"] = new JArray(options.Select(option => new JObject
                {
                    ["value"] = option["value"]!.DeepClone(),
                    ["label"] = option["label"].Text(option["value"]!.ToString())
                }));
            if (field["columns"] is JArray columns) entry["columns"] = Describe(columns);
            result.Add(field["key"].Text(), entry);
        }
        return result;
    }
}
