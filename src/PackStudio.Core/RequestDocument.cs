using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public static class RequestDocument
{
    public static ProjectDocument Parse(JObject input, PackageCatalog catalog)
    {
        var unknown = input.Properties().FirstOrDefault(p => p.Name is not ("template_id" or "design_name" or "overrides" or "material_assignments" or "custom_materials"));
        if (unknown != null)
            throw new ArgumentException($"未知请求字段 {unknown.Name}");
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

        document.Values = values;
        document.MaterialAssignments = input["material_assignments"]?.ToObject<Dictionary<string, string>>() ?? [];
        document.CustomMaterials = (input["custom_materials"] as JArray ?? []).Select(MaterialLibrary.Parse).ToList();
        return document;
    }
}
