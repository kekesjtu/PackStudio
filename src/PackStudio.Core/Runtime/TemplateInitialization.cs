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
        if (template.Info.Id is "chip_array" or "pbga_wb" && overrides?["substrate.layers"].Text() == "4-Layer")
            template.InitializeFourLayer(values, presetId);
        foreach (var rule in template.Data["initialization"] as JArray ?? [])
        {
            if (!JsonData.Matches(rule["when"] as JObject, selection)) continue;
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
