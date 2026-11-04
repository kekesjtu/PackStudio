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
        var overrides = input["overrides"] as JObject ?? new();
        var parameters = new JObject();
        foreach (var p in overrides.Properties())
        {
            string key = p.Name.StartsWith(id + ".", StringComparison.Ordinal) ? p.Name[(id.Length + 1)..] : "";
            if (!template.Fields.Any(f => f["key"].Text() == key))
                throw new ArgumentException($"未知参数 {p.Name}");
            parameters[key] = p.Value.DeepClone();
        }
        var document = ProjectDocument.Create(template, preset, input["design_name"].Text(template.Info.Name), parameters);
        document.MaterialAssignments = input["material_assignments"]?.ToObject<Dictionary<string, string>>() ?? [];
        document.CustomMaterials = (input["custom_materials"] as JArray ?? []).Select(MaterialLibrary.Parse).ToList();
        return document;
    }
}
