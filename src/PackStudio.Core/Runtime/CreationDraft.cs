using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public sealed class CreationDraft
{
    public Template Template { get; }
    public string PresetId { get; }
    public JObject Overrides { get; } = new();
    public JObject Values { get; private set; }
    public string? Error { get; private set; }

    public CreationDraft(Template template, string presetId, JObject? overrides = null)
    {
        Template = template;
        PresetId = presetId;
        foreach (var property in overrides?.Properties() ?? []) Overrides[property.Name] = property.Value.DeepClone();
        Values = Resolve(template, presetId, Overrides, false, out string? error);
        Error = error;
    }

    public IReadOnlySet<string> Set(string key, JToken value)
    {
        Overrides[key] = value.DeepClone();
        var previous = Values;
        Values = Resolve(Template, PresetId, Overrides, false, out string? error);
        Error = error;
        return Values.Properties().Where(p => !JToken.DeepEquals(previous[p.Name], p.Value)).Select(p => p.Name).ToHashSet();
    }

    public ProjectDocument Complete(string name) => Create(Template, PresetId, name, Overrides);

    internal static ProjectDocument Create(Template template, string presetId, string name, JObject? overrides)
    {
        name = name.Trim();
        ProjectDocument.ValidateName(name);
        var preset = template.Presets.FirstOrDefault(p => p.Name == presetId);
        var values = Resolve(template, presetId, overrides ?? new(), true, out _);
        values.Remove("footprint.size");
        return new() { TemplateId = template.Info.Id, Name = name, Values = values,
            MaterialAssignments = preset == null ? MaterialSelection.Defaults(template) : new(preset.MaterialAssignments),
            CustomMaterials = preset == null ? [] : [.. preset.CustomMaterials] };
    }

    static JObject Resolve(Template template, string presetId, JObject overrides, bool strict, out string? error)
    {
        var values = template.Defaults(presetId, overrides);
        try
        {
            values = ParameterRules.Prepare(template, values, overrides);
            if (strict) template.ValidateCreation(values);
            error = null;
        }
        catch (ArgumentException ex) when (!strict) { error = ex.Message; }
        return values;
    }
}
