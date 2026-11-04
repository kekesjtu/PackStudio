using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

/// <summary>Interprets initialization declarations; supplied overrides always retain their intent.</summary>
public static class TemplateInitialization
{
    public static JObject Create(Template template, string presetId, JObject? overrides = null)
    {
        var values = template.PresetDefaults(presetId);
        var selection = (JObject)values.DeepClone();
        Overlay(selection, overrides);
        var preset = template.Presets.FirstOrDefault(p => p.Id == presetId);
        foreach (var rule in template.Data["initialization"] as JArray ?? [])
        {
            if (!JsonData.Matches(rule["when"] as JObject, selection)) continue;
            if (rule["branch"] is JValue branch)
            {
                var source = preset?.Branches[branch.Text()]?["values"] as JObject
                    ?? throw new InvalidDataException($"预设 {presetId} 缺少分支 {branch}。");
                foreach (var key in (JArray)rule["fields"]!)
                    values[key.Text()] = source[key.Text()]?.DeepClone()
                        ?? throw new InvalidDataException($"分支 {branch} 缺少参数 {key}。");
            }
            Overlay(values, rule["set"] as JObject);
            if (rule["copy"] is JObject copies)
                foreach (var copy in copies.Properties())
                    values[copy.Name] = selection[copy.Value.Text()]?.DeepClone() ?? JValue.CreateNull();
        }
        Overlay(values, overrides);
        return values;
    }

    static void Overlay(JObject target, JObject? source)
    {
        foreach (var property in source?.Properties() ?? [])
            target[property.Name] = property.Value.DeepClone();
    }
}
