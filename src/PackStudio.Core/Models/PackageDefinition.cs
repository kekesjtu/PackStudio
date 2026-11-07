using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public sealed class PackageDefinition
{
    public TemplateInfo Info { get; }
    public JObject Data { get; }
    public JArray Fields { get; }
    public JArray DisplayFields { get; }
    public JArray MaterialSelections { get; }
    public JArray Steps => (JArray)Data["steps"]!;
    public IReadOnlyList<ProjectDocument> Presets { get; }
    public string DefaultPreset => Fields.FirstOrDefault(f => f["type"].Text() == "footprint")?["default"].Text() ?? "";
    public bool HasFootprint => Fields.Any(f => f["type"].Text() == "footprint");
    public IEnumerable<JToken> CreationFields => Fields.Where(f => f["creation_option"].Flag());

    public PackageDefinition(TemplateInfo info, JObject data, IReadOnlyList<ProjectDocument> presets)
    {
        Info = info;
        Data = data;
        Presets = presets;
        Fields = (JArray)data["keys"]!;
        DisplayFields = new(Fields.Where(f => f["step"]?.Type == JTokenType.String));
        MaterialSelections = (JArray)data["materials"]!;
    }

    public JArray OptionsFor(JToken field) => field["options_source"].Text() switch
    {
        "presets" => new JArray(Presets.Select(p => new JObject { ["value"] = p.Name, ["label"] = p.Name })),
        "" => field["options"] as JArray ?? [],
        var source => throw new InvalidDataException($"未知选项来源 {source}。")
    };

    public static JArray OptionValues(JToken field) => new((field["options"] as JArray ?? [])
        .Select(option => option["value"]?.DeepClone() ?? throw new InvalidDataException($"参数 {field["key"]} 的选项缺少 value。")));

    public string ParameterDisplayName(string path, JObject values) => ResolveDisplayName(Fields, path, values);

    static string ResolveDisplayName(JArray fields, string path, JObject values)
    {
        // Parameter keys can contain dots; match the complete key before resolving table columns.
        var field = fields.OrderByDescending(f => f["key"].Text().Length).FirstOrDefault(f =>
        {
            string key = f["key"].Text();
            return path == key || path.StartsWith(key + "[");
        });
        if (field == null) return "参数";
        string label = TemplateSymbols.Resolve(field, values);
        if (string.IsNullOrWhiteSpace(label)) label = field["label"].Text();
        if (string.IsNullOrWhiteSpace(label)) label = "参数";
        string remaining = path[field["key"].Text().Length..];
        if (remaining.StartsWith('['))
        {
            int end = remaining.IndexOf(']');
            if (end < 0 || !int.TryParse(remaining[1..end], out int row) || row < 0) return label;
            label += $"第 {row + 1} 行";
            remaining = remaining[(end + 1)..];
            if (field["columns"] is JArray columns && remaining.StartsWith('.') && remaining.Length > 1)
                label += " · " + ResolveDisplayName(columns, remaining[1..], values);
        }
        return label;
    }

    /// <summary>Display values only; does not apply creation branches or derive a layer stack.</summary>
    public JObject DisplayDefaults(string presetId)
    {
        var preset = Presets.FirstOrDefault(p => p.Name == presetId);
        if (Presets.Count > 0 && preset == null)
            throw new ArgumentException($"未知外形预设 {presetId}");
        var values = preset == null
            ? new JObject(Fields.Select(f => new JProperty(f["key"].Text(), f["default"]?.DeepClone() ?? JValue.CreateNull())))
            : (JObject)preset.Values.DeepClone();
        var footprint = Fields.FirstOrDefault(f => f["type"].Text() == "footprint");
        if (footprint != null) values[footprint["key"].Text()] = presetId;
        return values;
    }
}
