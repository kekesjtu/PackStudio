using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static class TemplateSymbols
{
    public static string Resolve(JToken field, JObject values)
    {
        var symbol = field["des_symbol"];
        return symbol is JObject mapping ? mapping["cases"]?[values[mapping["selector"].Text()].Text()].Text() ?? "" : symbol.Text();
    }
    public static IEnumerable<string> Dependencies(JToken field) => field["des_symbol"] is JObject mapping ? [mapping["selector"].Text()] : [];
}
