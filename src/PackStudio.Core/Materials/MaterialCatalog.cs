using System.Collections.ObjectModel;

namespace PackStudio.Core;

public sealed class MaterialCatalog(IEnumerable<Material> materials)
{
    public IReadOnlyDictionary<string, Material> Items { get; } = new ReadOnlyDictionary<string, Material>(materials.ToDictionary(m => m.Id));
}
