using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public sealed class CreationDraft
{
    public Template Template { get; }
    public string PresetId { get; }
    public JObject Overrides { get; } = new();
    public JObject Values { get; private set; }
    public string? Error { get; private set; }

    public CreationDraft(Template template, string presetId)
    {
        Template = template;
        PresetId = presetId;
        Values = Evaluate(false);
    }

    public IReadOnlySet<string> Set(string key, JToken value)
    {
        Overrides[key] = value.DeepClone();
        var previous = Values;
        Values = Evaluate(false);
        return Values.Properties().Where(p => !JToken.DeepEquals(previous[p.Name], p.Value)).Select(p => p.Name).ToHashSet();
    }

    public ProjectDocument Complete(string name)
    {
        name = name.Trim();
        ProjectDocument.ValidateName(name);
        return new() { TemplateId = Template.Info.Id, PresetId = PresetId, Name = name, Values = Evaluate(true) };
    }

    JObject Evaluate(bool strict)
    {
        var values = Template.Defaults(PresetId, Overrides);
        try
        {
            values = ParameterRules.Prepare(Template, values, Overrides);
            if (strict) Template.ValidateCreation(values);
            Error = null;
        }
        catch (ArgumentException ex) when (!strict) { Error = ex.Message; }
        return values;
    }
}
