using System.Collections.ObjectModel;

namespace PackStudio.Core;

public sealed class MaterialCatalog
{
    public IReadOnlyDictionary<string, Material> Items { get; }

    public MaterialCatalog(IEnumerable<Material> materials)
    {
        var items = materials.ToDictionary(m => m.Id);
        foreach (var material in items.Values)
        {
            string[] errors = FieldRules.MaterialErrors(material).ToArray();
            if (errors.Length > 0) throw new InvalidDataException($"材料 {material.Name}：{string.Join(" ", errors)}");
        }
        Items = new ReadOnlyDictionary<string, Material>(items);
    }
}
