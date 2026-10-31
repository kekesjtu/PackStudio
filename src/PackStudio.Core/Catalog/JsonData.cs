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
        byte[] bytes = File.ReadAllBytes(path);
        string hash = Convert.ToHexStringLower(System.Security.Cryptography.SHA256.HashData(bytes));
        if (hash != entry["sha256"].Text())
            throw new InvalidDataException($"运行数据哈希不匹配：{entry["file"]}");
        return JObject.Parse(System.Text.Encoding.UTF8.GetString(bytes));
    }

    public static JToken? At(JToken? token, IEnumerable<string> path)
    {
        foreach (var part in path)
            token = token?[part];
        return token;
    }

    public static double Number(this JToken? token, double fallback = 0) => token == null || token.Type == JTokenType.Null ? fallback : token.Value<double>();
    public static string Text(this JToken? token, string fallback = "") => token == null || token.Type == JTokenType.Null ? fallback : token.Value<string>() ?? fallback;
    public static bool Flag(this JToken? token) => token?.Type == JTokenType.Boolean && token.Value<bool>();
    public static bool Matches(JObject? rules, JObject values) => rules == null || rules.Properties().All(p => JToken.DeepEquals(p.Value, values[p.Name]));
}

public sealed record TemplateInfo(string Id, string Name);
public sealed record Preset(string Id, JObject Values, JObject Materials, JObject Bga, JObject Record);
public sealed class Template(TemplateInfo info, JObject data, IReadOnlyList<Preset> presets)
{
    public TemplateInfo Info { get; } = info;
    public JObject Data { get; } = data;
    public IReadOnlyList<Preset> Presets { get; } = presets;
    public JArray Fields => (JArray)Data["fields"]!;
    public JArray MaterialSelections => (JArray)Data["material_selections"]!;
    public string DefaultPreset => Fields.FirstOrDefault(f => f["control"].Text() == "footprint")?["default"].Text() ?? "";

    public JObject Defaults(string presetId)
    {
        var values = new JObject(Fields.Select(f => new JProperty(f["key"]!.ToString(), f["default"]?.DeepClone() ?? JValue.CreateNull())));
        var preset = Presets.FirstOrDefault(p => p.Id == presetId);
        if (Presets.Count > 0 && preset == null)
            throw new ArgumentException($"未知外形预设 {presetId}");
        var footprint = Fields.FirstOrDefault(f => f["control"].Text() == "footprint");
        if (footprint != null)
            values[footprint["key"].Text()] = presetId;
        if (preset != null)
            foreach (var p in preset.Values.Properties())
                values[p.Name] = p.Value.DeepClone();
        return values;
    }

    public void Validate(JObject values)
    {
        foreach (var f in Fields)
        {
            if (!JsonData.Matches(f["visible_when"] as JObject, values) || !JsonData.Matches(f["enabled_when"] as JObject, values))
                continue;
            string key = f["key"]!.ToString(), control = f["control"].Text();
            var v = values[key];
            if (v == null || v.Type == JTokenType.Null)
                continue;
            if (control is "number" or "integer" or "integer_spinbox")
            {
                if (v.Type is not (JTokenType.Integer or JTokenType.Float))
                    throw new ArgumentException($"{f["label"]} 必须是数字。");
                double n = v.Value<double>();
                if (!double.IsFinite(n) || control.StartsWith("integer") && n != Math.Truncate(n) || n < (f["minimum"]?.Type is JTokenType.Integer or JTokenType.Float ? f["minimum"]!.Number() : 0) || f["maximum"]?.Type != JTokenType.Null && f["maximum"] != null && n > f["maximum"].Number())
                    throw new ArgumentException($"{f["label"]} 超出允许范围。");
            }

            if (control == "checkbox" && v.Type != JTokenType.Boolean)
                throw new ArgumentException($"{f["label"]} 必须是布尔值。");
            var options = f["options"] as JArray;
            if (options?.Count > 0 && !options.Any(o => JToken.DeepEquals(o, v)))
                throw new ArgumentException($"{f["label"]} 选项无效。");
        }
    }
}
