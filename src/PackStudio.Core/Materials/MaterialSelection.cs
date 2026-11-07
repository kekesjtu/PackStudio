using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public sealed record MaterialChoices(string SelectedId, IReadOnlyList<Material> Items);

public static class MaterialSelection
{
    public static bool Allows(JToken selection, string id) => selection["options"] == null
        ? id.Length > 0
        : PackageDefinition.OptionValues(selection).Any(o => o.Text() == id || id.Length > 0 && o.Text() == "*");

    public static IReadOnlyList<Material> Available(MaterialCatalog catalog, PackageDefinition template, ProjectDocument document, PackageModel? model = null)
    {
        var materials = catalog.Items.Values.ToDictionary(m => m.Id);
        IReadOnlyDictionary<string, Material> modeled = model?.TemplateId == document.TemplateId ? model.Materials : new Dictionary<string, Material>();
        foreach (var m in modeled.Values) materials[m.Id] = m;
        foreach (var m in document.CustomMaterials) materials[m.Id] = m;
        var custom = document.CustomMaterials.Select(m => m.Id).ToHashSet();
        var assigned = document.MaterialAssignments.Values.ToHashSet();
        return materials.Values.GroupBy(m => m.Name).Select(g => g
            .OrderByDescending(m => assigned.Contains(m.Id))
            .ThenByDescending(m => custom.Contains(m.Id))
            .ThenByDescending(m => modeled.ContainsKey(m.Id))
            .ThenBy(m => m.Id.Length).ThenBy(m => m.Id, StringComparer.Ordinal).First()).ToList();
    }

    public static MaterialChoices Choices(MaterialCatalog catalog, PackageDefinition template, ProjectDocument document, JToken selection, PackageModel? model = null)
    {
        string id = document.MaterialAssignments.GetValueOrDefault(selection["key"].Text(), "");
        var representatives = Available(catalog, template, document, model);
        var candidates = catalog.Items.Values.Concat(document.CustomMaterials)
            .Concat(model?.Materials.Values ?? []);
        var allowedNames = candidates.Where(m => Allows(selection, m.Id) || m.Id == id).Select(m => m.Name).ToHashSet();
        var selected = document.CustomMaterials.FirstOrDefault(m => m.Id == id)
            ?? model?.Materials.GetValueOrDefault(id) ?? catalog.Items.GetValueOrDefault(id);
        var allowed = representatives.Where(m => allowedNames.Contains(m.Name)).ToList();
        return new(allowed.FirstOrDefault(m => m.Name == selected?.Name)?.Id ?? id, allowed);
    }
}
