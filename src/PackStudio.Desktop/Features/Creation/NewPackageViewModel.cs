using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Desktop;

/// <summary>The selections and submitted values in the New Package dialog.</summary>
public sealed class NewPackageViewModel
{
    public PackageDefinition Template { get; }
    public string PresetId { get; }
    public string Name { get; set; }
    public JObject Values { get; } = new();
    public JObject Overrides { get; } = new();

    public NewPackageViewModel(PackageDefinition template, string presetId)
    {
        Template = template;
        PresetId = presetId;
        Name = template.Info.Name;
        var defaults = template.DisplayDefaults(presetId);
        foreach (var field in template.CreationFields)
        {
            string key = field["key"].Text();
            Values[key] = defaults[key]?.DeepClone() ?? JValue.CreateNull();
        }
    }

    public IReadOnlySet<string> Set(string path, JToken value)
    {
        if (JToken.DeepEquals(Values[path], value) && Overrides.Property(path) != null) return new HashSet<string>();
        Values[path] = value.DeepClone();
        Overrides[path] = value.DeepClone();
        return new HashSet<string> { path };
    }
}
