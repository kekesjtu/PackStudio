using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;

internal static class DesFieldLabels
{
    static readonly JObject Fields = JsonData.Read(System.IO.Path.Combine(App.DataRoot, "des_field_labels.json"));

    // 映射值可以是 DES 键字符串，也可以是按基板层数（substrate.layers）选择的 DES 键对象。
    internal static string Symbol(string family, string key, string substrateLayers)
    {
        JToken? entry = Fields[family]?[key];
        return entry is JObject choices ? choices[substrateLayers].Text() : entry.Text();
    }
}
