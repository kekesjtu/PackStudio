using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public sealed class PackageDefinition
{
    public TemplateInfo Info { get; }
    public JObject Data { get; }
    public JArray Fields => (JArray)Data["fields"]!;
    public JArray MaterialSelections => (JArray)Data["material_selections"]!;
    public IReadOnlyList<Material> BaselineMaterials { get; }
    public IReadOnlyList<ProjectDocument> Presets { get; }
    public UiTemplate Ui { get; }
    public string DefaultPreset => Fields.FirstOrDefault(f => f["type"].Text() == "footprint")?["default"].Text() ?? "";
    public bool HasFootprint => Fields.Any(f => f["type"].Text() == "footprint");
    public IEnumerable<JToken> CreationFields => Ui.Fields.Where(f => f["creation_option"].Flag());

    public PackageDefinition(TemplateInfo info, JObject data, IReadOnlyList<ProjectDocument> presets,
        UiTemplate ui, IReadOnlyList<Material> baselineMaterials)
    {
        Info = info;
        Data = data;
        Presets = presets;
        Ui = ui;
        BaselineMaterials = baselineMaterials;
    }

    public JArray OptionsFor(JToken field) => field["options_source"].Text() switch
    {
        "presets" => new JArray(Presets.Select(p => p.Name)),
        "" => field["options"] as JArray ?? [],
        var source => throw new InvalidDataException($"未知选项来源 {source}。")
    };

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
