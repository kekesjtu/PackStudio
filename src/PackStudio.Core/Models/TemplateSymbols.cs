using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static class TemplateSymbols
{
    public static string Resolve(JToken field, JObject values)
    {
        var symbol = field["des_symbol"];
        if (symbol is not JObject mapping) return symbol.Text();
        var selection = values[mapping["selector"].Text()];
        return selection is JValue ? mapping["cases"]?[selection.Text()].Text() ?? "" : "";
    }
    public static IEnumerable<string> Dependencies(JToken field) => field["des_symbol"] is JObject mapping ? [mapping["selector"].Text()] : [];
}
