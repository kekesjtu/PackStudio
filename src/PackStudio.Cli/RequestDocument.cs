using Newtonsoft.Json.Linq;
using PackStudio.Core;

namespace PackStudio.Cli;
public static class RequestDocument
{
    public static ProjectDocument Parse(JObject input, RuntimeDataCatalog catalog)
    {
        var unknown = input.Properties().FirstOrDefault(p => p.Name is not ("template_id" or "design_name" or "overrides" or "material_assignments" or "custom_materials"));
        if (unknown != null)
            throw new ArgumentException($"未知请求字段 {unknown.Name}");
        string id = input["template_id"].Text();
        var template = catalog.Load(id);
        if (input["overrides"] is { } submitted && submitted is not JObject ||
            input["material_assignments"] is { } selections && (selections is not JObject groups || groups.Properties().Any(p => p.Value.Type != JTokenType.String)) ||
            input["custom_materials"] is { } materials && (materials is not JArray records || records.Any(r => r is not JObject)))
            throw new InvalidDataException("overrides 和 material_assignments 必须为对象，材料选择必须为字符串，custom_materials 必须为材料对象数组。");
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
        var selection = parameters["substrate.layers"] ?? template.DisplayDefaults(preset)["substrate.layers"];
        var fourLayer = id is "chip_array" or "pbga_wb" && selection is { Type: JTokenType.String } && selection.Value<string>() == "4-Layer" ? catalog.LoadFourLayer(id) : null;
        var padSelection = parameters["package.exposed_pad"] ?? template.DisplayDefaults(preset)["package.exposed_pad"];
        var exposedPad = id is "sop" or "pqfp" && padSelection.Flag() ? catalog.LoadExposedPad(id) : null;
        var document = PackageInitializer.Create(template, preset, input["design_name"].Text(template.Info.Name), parameters, fourLayer, exposedPad);
        foreach (var pair in input["material_assignments"]?.ToObject<Dictionary<string, string>>() ?? [])
            document.MaterialAssignments[pair.Key] = pair.Value;
        foreach (var source in input["custom_materials"] as JArray ?? [])
        {
            var material = (JObject)source.DeepClone();
            if (material.Property("conduct_type") == null)
            {
                var conductivity = material["conductivity"] as JObject ?? throw new InvalidDataException("自定义材料缺少导热率对象。");
                bool isotropic = JToken.DeepEquals(conductivity["x"], conductivity["y"]) && JToken.DeepEquals(conductivity["y"], conductivity["z"]);
                material["conduct_type"] = isotropic && material["conductivity_coefficient"]?.Type is JTokenType.Integer or JTokenType.Float ? 1 : isotropic ? 0 : 2;
            }
            document.CustomMaterials.Add(MaterialCatalogReader.Parse(material));
        }
        return document;
    }
}
