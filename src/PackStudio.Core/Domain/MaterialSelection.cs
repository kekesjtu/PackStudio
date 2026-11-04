using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public sealed record MaterialChoices(string SelectedId, IReadOnlyList<Material> Items);

public static class MaterialSelection
{
    public static Dictionary<string, string> Resolve(Template template, string presetId, IReadOnlyDictionary<string, string>? overrides = null)
    {
        var result = template.MaterialSelections.ToDictionary(s => s["group_id"].Text(), s => s["default"].Text());
        var preset = template.Presets.FirstOrDefault(p => p.Id == presetId);
        foreach (var property in preset?.MaterialAssignments.Properties() ?? []) result[property.Name] = property.Value.Text();
        foreach (var pair in overrides ?? new Dictionary<string, string>())
        {
            var selection = template.MaterialSelections.SingleOrDefault(s => s["group_id"].Text() == pair.Key)
                ?? throw new ArgumentException($"未知材料组 {pair.Key}");
            if (!((JArray)selection["options"]!).Any(o => o.Text() == "*" || o.Text() == pair.Value) &&
                !template.Presets.Any(p => p.MaterialAssignments[pair.Key].Text() == pair.Value))
                throw new ArgumentException($"材料 {pair.Value} 不适用于 {pair.Key}");
            result[pair.Key] = pair.Value;
        }
        return result;
    }

    public static MaterialChoices Choices(PackageCatalog catalog, Template template, ProjectDocument document, JToken selection)
    {
        string group = selection["group_id"].Text();
        var options = (JArray)selection["options"]!;
        string id = Resolve(template, document.PresetId, document.MaterialAssignments)[group];
        var allowed = catalog.Materials.Items.Values.Where(m => options.Any(o => o.Text() == "*" || o.Text() == m.Id)).ToList();
        if (id.Length > 0 && allowed.All(m => m.Id != id) && catalog.Materials.Items.TryGetValue(id, out var current)) allowed.Add(current);
        allowed = allowed.GroupBy(m => m.Name).Select(g => g.FirstOrDefault(m => m.Id == id) ?? g.OrderBy(m => m.Id.Length).ThenBy(m => m.Id).First()).ToList();
        return new(id, allowed.Select(m => document.CustomMaterials.FirstOrDefault(c => c.Id == m.Id) ?? m).ToList());
    }
}
