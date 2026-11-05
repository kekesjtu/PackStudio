using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public sealed class PackageDefinition
{
    public TemplateInfo Info { get; }
    public JObject Data { get; }
    public JArray Keys => (JArray)Data["keys"]!;
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
        Fields = new(Keys.Where(f => f["type"].Text() != "material"));
        DisplayFields = new(Fields.Where(f => f["step"]?.Type == JTokenType.String));
        MaterialSelections = new(Keys.Where(f => f["type"].Text() == "material"));
    }

    public JArray OptionsFor(JToken field) => field["options_source"].Text() switch
    {
        "presets" => new JArray(Presets.Select(p => new JObject { ["value"] = p.Name, ["label"] = p.Name })),
        "" => field["options"] as JArray ?? [],
        var source => throw new InvalidDataException($"未知选项来源 {source}。")
    };

    public static JArray OptionValues(JToken field) => new((field["options"] as JArray ?? [])
        .Select(option => option["value"]?.DeepClone() ?? throw new InvalidDataException($"参数 {field["key"]} 的选项缺少 value。")));

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
