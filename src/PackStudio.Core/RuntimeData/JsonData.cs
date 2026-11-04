using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public static class JsonData
{
    public static JObject Read(string path) => JObject.Parse(File.ReadAllText(path));
    public static JObject CatalogEntry(string directory, JToken entry)
    {
        string root = Path.GetFullPath(directory) + Path.DirectorySeparatorChar;
        string path = Path.GetFullPath(Path.Combine(directory, entry["file"].Text()));
        if (!path.StartsWith(root, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("目录记录超出运行库。");
        return Read(path);
    }

    public static double Number(this JToken? token, double fallback = 0) => token == null || token.Type == JTokenType.Null ? fallback : token.Value<double>();
    public static string Text(this JToken? token, string fallback = "") => token == null || token.Type == JTokenType.Null ? fallback : token.Value<string>() ?? fallback;
    public static bool Flag(this JToken? token) => token?.Type == JTokenType.Boolean && token.Value<bool>();
    public static bool Matches(JObject? rules, JObject values) => rules == null || rules.Properties().All(p => JToken.DeepEquals(p.Value, values[p.Name]));
}
