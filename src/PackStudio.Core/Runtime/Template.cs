using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public sealed record Preset(string Id, JObject Values, JObject MaterialAssignments, JObject Branches);
public sealed class Template
{
    public TemplateInfo Info { get; }
    public JObject Data { get; }
    public IReadOnlyList<Preset> Presets { get; }
    public Template(TemplateInfo info, JObject data, IReadOnlyList<Preset> presets)
    {
        Info = info; Data = data; Presets = presets;
        ValidateDefinitions(Fields);
    }
    public JArray Fields => (JArray)Data["fields"]!;
    public JArray MaterialSelections => (JArray)Data["material_selections"]!;
    public string DefaultPreset => Fields.FirstOrDefault(f => f["control"].Text() == "footprint")?["default"].Text() ?? "";

    public JArray Steps => (JArray)Data["steps"]!;
    public IEnumerable<JToken> CreationFields => Fields.Where(f => f["creation_option"].Flag());
    public JObject Defaults(string presetId, JObject? overrides = null) => TemplateInitialization.Create(this, presetId, overrides);
    public JArray OptionsFor(JToken field) => field["options_source"].Text() switch
    {
        "presets" => new JArray(Presets.Select(p => p.Id)),
        "" => field["options"] as JArray ?? [],
        var source => throw new InvalidDataException($"未知选项来源 {source}。")
    };

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

    public void Validate(JObject values, bool forCreation = false)
    {
        ValidateStructure(Fields, values);
        ValidateFields(Fields, values, forCreation);
    }
    public bool HasFootprint => Fields.Any(f => f["control"].Text() == "footprint");
    public void ValidateCreation(JObject values)
    {
        Validate(values, forCreation: true);
        foreach (var f in CreationFields.Where(f => JsonData.Matches(f["visible_when"] as JObject, values) && JsonData.Matches(f["enabled_when"] as JObject, values)))
            if (values[f["key"].Text()]?.Type is null or JTokenType.Null)
                throw new ArgumentException($"请填写{f["label"]}。");
    }

    static void ValidateDefinitions(JArray fields)
    {
        foreach (var f in fields)
        {
            if (f["control"].Text() != "object") continue;
            if (f["default"] is not JObject defaults || f["fields"] is not JArray children)
                throw new InvalidDataException($"对象字段 {f["key"]} 必须声明默认对象与子字段。");
            ValidateDefinitions(children);
            ValidateStructure(children, defaults);
        }
    }

    static void ValidateStructure(JArray fields, JObject values)
    {
        foreach (var f in fields.Where(f => f["control"].Text() == "object"))
        {
            if (values[f["key"].Text()] is not JObject nested)
                throw new ArgumentException($"{f["label"]} 必须是对象。");
            ValidateStructure((JArray)f["fields"]!, nested);
        }
    }

    void ValidateFields(JArray fields, JObject values, bool forCreation)
    {
        foreach (var f in fields)
        {
            if (!forCreation && f["creation_only"].Flag()) continue;
            if (!JsonData.Matches(f["visible_when"] as JObject, values) || !JsonData.Matches(f["enabled_when"] as JObject, values))
                continue;
            string key = f["key"]!.ToString(), control = f["control"].Text();
            var v = values[key];
            if (v == null || v.Type == JTokenType.Null)
                continue;
            if (FieldValues.Error(f, v, OptionsFor(f)) is string error) throw new ArgumentException(error);
            if (control == "object")
                ValidateFields((JArray)f["fields"]!, (JObject)v, forCreation);
            if (control is "table" or "removal_matrix" && v is not JArray)
                throw new ArgumentException($"{f["label"]} 必须是数组。");

        }
    }
}
