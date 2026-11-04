using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public sealed record MaterialChoices(string SelectedId, IReadOnlyList<Material> Items);

public static class MaterialSelection
{
    public static Dictionary<string, string> Defaults(Template template) =>
        template.MaterialSelections.ToDictionary(s => s["group_id"].Text(), s => s["default"].Text());

    public static Dictionary<string, string> Resolve(Template template, IReadOnlyDictionary<string, string> assignments)
    {
        var result = new Dictionary<string, string>(assignments);
        foreach (var selection in template.MaterialSelections)
            if (!result.ContainsKey(selection["group_id"].Text()))
                throw new ArgumentException($"缺少材料组 {selection["group_id"]} 的选择。");
        foreach (var pair in assignments)
        {
            var selection = template.MaterialSelections.SingleOrDefault(s => s["group_id"].Text() == pair.Key)
                ?? throw new ArgumentException($"未知材料组 {pair.Key}");
            if (!((JArray)selection["options"]!).Any(o => o.Text() == "*" || o.Text() == pair.Value))
                throw new ArgumentException($"材料 {pair.Value} 不适用于 {pair.Key}");
            result[pair.Key] = pair.Value;
        }
        return result;
    }

    public static IReadOnlyList<Material> Available(PackageCatalog catalog, Template template, ProjectDocument document, PackageModel? model = null)
    {
        var materials = catalog.Materials.Items.Values.ToDictionary(m => m.Id);
        var modeled = model?.TemplateId == document.TemplateId ? model.Materials : [];
        foreach (var m in modeled.Values) materials[m.Id] = m;
        foreach (var m in document.CustomMaterials) materials[m.Id] = m;
        var custom = document.CustomMaterials.Select(m => m.Id).ToHashSet();
        var assigned = Resolve(template, document.MaterialAssignments).Values.ToHashSet();
        return materials.Values.GroupBy(m => m.Name).Select(g => g
            .OrderByDescending(m => assigned.Contains(m.Id))
            .ThenByDescending(m => custom.Contains(m.Id))
            .ThenByDescending(m => modeled.ContainsKey(m.Id))
            .ThenBy(m => m.Id.Length).ThenBy(m => m.Id, StringComparer.Ordinal).First()).ToList();
    }

    public static MaterialChoices Choices(PackageCatalog catalog, Template template, ProjectDocument document, JToken selection, PackageModel? model = null)
    {
        string id = Resolve(template, document.MaterialAssignments)[selection["group_id"].Text()];
        var options = (JArray)selection["options"]!;
        var representatives = Available(catalog, template, document, model);
        var allowedNames = catalog.Materials.Items.Values.Where(m => options.Any(o => o.Text() == "*" || o.Text() == m.Id) || m.Id == id).Select(m => m.Name).ToHashSet();
        var selected = document.CustomMaterials.FirstOrDefault(m => m.Id == id)
            ?? model?.Materials.GetValueOrDefault(id) ?? catalog.Materials.Items.GetValueOrDefault(id);
        var allowed = representatives.Where(m => allowedNames.Contains(m.Name)).ToList();
        return new(allowed.FirstOrDefault(m => m.Name == selected?.Name)?.Id ?? id, allowed);
    }
}
