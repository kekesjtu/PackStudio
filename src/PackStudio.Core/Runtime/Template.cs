using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public sealed record Preset(string Id, JObject Values, JObject MaterialAssignments, JObject Branches);
public sealed class Template(TemplateInfo info, JObject data, IReadOnlyList<Preset> presets)
{
    public TemplateInfo Info { get; } = info;
    public JObject Data { get; } = data;
    public IReadOnlyList<Preset> Presets { get; } = presets;
    public JArray Fields => (JArray)Data["fields"]!;
    public JArray MaterialSelections => (JArray)Data["material_selections"]!;
    public string DefaultPreset => Fields.FirstOrDefault(f => f["control"].Text() == "footprint")?["default"].Text() ?? "";

    public JArray Steps => (JArray)Data["steps"]!;
    public IEnumerable<JToken> CreationFields => Fields.Where(f => f["creation_option"].Flag());
    public JObject Defaults(string presetId, JObject? overrides = null) => TemplateInitialization.Create(this, presetId, overrides);

    internal JObject PresetDefaults(string presetId)
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

    public void Validate(JObject values) => ValidateFields(Fields, values);
    public bool HasFootprint => Fields.Any(f => f["control"].Text() == "footprint");
    public void ValidateCreation(JObject values)
    {
        Validate(values);
        foreach (var f in CreationFields.Where(f => JsonData.Matches(f["visible_when"] as JObject, values) && JsonData.Matches(f["enabled_when"] as JObject, values)))
            if (values[f["key"].Text()]?.Type is null or JTokenType.Null)
                throw new ArgumentException($"请填写{f["label"]}。");
    }

    static void ValidateFields(JArray fields, JObject values)
    {
        foreach (var f in fields)
        {
            if (!JsonData.Matches(f["visible_when"] as JObject, values) || !JsonData.Matches(f["enabled_when"] as JObject, values))
                continue;
            string key = f["key"]!.ToString(), control = f["control"].Text();
            var v = values[key];
            if (control == "object" && v is not JObject) throw new ArgumentException($"{f["label"]} 必须是对象。");
            if (v == null || v.Type == JTokenType.Null)
                continue;
            if (FieldValues.Error(f, v) is string error) throw new ArgumentException(error);
            if (control == "object")
            {
                if (v is not JObject nested) throw new ArgumentException($"{f["label"]} 必须是对象。");
                ValidateFields((JArray)f["fields"]!, nested);
            }
            if (control is "table" or "removal_matrix" && v is not JArray)
                throw new ArgumentException($"{f["label"]} 必须是数组。");

        }
    }
}
