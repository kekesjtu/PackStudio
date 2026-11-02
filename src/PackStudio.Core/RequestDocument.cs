using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public static class RequestDocument
{
    public static ProjectDocument Parse(JObject input, PackageCatalog catalog)
    {
        string id = input["template_id"].Text();
        var template = catalog.Load(id);
        string preset = input["overrides"]?[id + ".footprint.size"].Text(template.DefaultPreset) ?? template.DefaultPreset;
        var document = ProjectDocument.Create(template, preset, input["design_name"].Text(template.Info.Name));
        var values = document.Values;
        var overrides = input["overrides"] as JObject ?? new();
        if (overrides[id + ".substrate.layers"] != null)
            values["substrate.layers"] = overrides[id + ".substrate.layers"]!.DeepClone();
        values = catalog.Initialize(template, values, preset);
        foreach (var p in overrides.Properties())
        {
            if (!p.Name.StartsWith(id + ".", StringComparison.Ordinal) || values.Property(p.Name[(id.Length + 1)..]) == null)
                throw new ArgumentException($"未知参数 {p.Name}");
            values[p.Name[(id.Length + 1)..]] = p.Value.DeepClone();
        }

        if (input["die_power_w"]?.Type is JTokenType.Integer or JTokenType.Float)
            values["die.power"] = input["die_power_w"]!.DeepClone();
        document.Values = values;
        document.MaterialAssignments = input["material_assignments"]?.ToObject<Dictionary<string, string>>() ?? [];
        document.CustomMaterials = (input["custom_materials"] as JArray ?? []).Select(MaterialLibrary.Parse).ToList();
        return document;
    }
}
