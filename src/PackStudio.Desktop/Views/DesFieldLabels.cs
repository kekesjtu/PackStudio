using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;

internal static class DesFieldLabels
{
    internal static string Symbol(JToken field, string substrateLayers)
    {
        JToken? entry = field["des_symbol"];
        return entry is JObject choices ? choices[substrateLayers].Text() : entry.Text();
    }
}
