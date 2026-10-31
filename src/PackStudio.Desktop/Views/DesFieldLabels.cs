using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;

internal static class DesFieldLabels
{
    static readonly JObject Fields = JsonData.Read(System.IO.Path.Combine(App.DataRoot, "des_field_labels.json"));
    internal static string Symbol(string family, string key, string label)
    {
        string symbol = Fields[family]?[key].Text() ?? "";
        return symbol;
    }
}
