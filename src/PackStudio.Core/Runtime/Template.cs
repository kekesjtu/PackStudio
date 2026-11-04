using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public sealed record TemplateInfo(string Id, string Name);
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

    public JObject Restore(string presetId, JObject saved)
    {
        var values = Defaults(presetId, saved);
        foreach (var field in Fields.Where(f => f["control"].Text() == "object"))
        {
            string key = field["key"].Text();
            if (values[key]?.Type is null or JTokenType.Null)
                values[key] = field["default"]!.DeepClone();
            if (values[key] is JObject nested && field["default"] is JObject defaults)
                foreach (var property in defaults.Properties())
                    if (nested.Property(property.Name) == null) nested[property.Name] = property.Value.DeepClone();
        }
        return values;
    }

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
                if (p.Value.Type != JTokenType.Null || Fields.All(f => f["key"].Text() != p.Name || f["control"].Text() != "object"))
                    values[p.Name] = p.Value.DeepClone();
        return values;
    }

    public void Validate(JObject values) => ValidateFields(Fields, values);

    static void ValidateFields(JArray fields, JObject values)
    {
        foreach (var f in fields)
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
            if (control == "object")
            {
                if (v is not JObject nested) throw new ArgumentException($"{f["label"]} 必须是对象。");
                ValidateFields((JArray)f["fields"]!, nested);
            }
            if (control is "table" or "removal_matrix" && v is not JArray)
                throw new ArgumentException($"{f["label"]} 必须是数组。");
            var options = f["options"] as JArray;
            if (options?.Count > 0 && !options.Any(o => JToken.DeepEquals(o, v)))
                throw new ArgumentException($"{f["label"]} 选项无效。");
        }
    }
}
