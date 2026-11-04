using Newtonsoft.Json.Linq;
using System.Collections.Concurrent;

namespace PackStudio.Core;
public sealed class PackageCatalog
{
    public IReadOnlyList<TemplateInfo> Families { get; }
    public TemplateInfo DefaultFamily => Families.Single(f => f.IsDefault);
    readonly string root;
    readonly JObject index;
    readonly ConcurrentDictionary<string, Template> cache = new();
    public MaterialLibrary Materials { get; }
    public IReadOnlyDictionary<string, ModelGroup> Groups { get; }

    public PackageCatalog(string root)
    {
        this.root = Path.GetFullPath(root);
        Materials = new(root);
        Groups = JsonData.Read(Path.Combine(root, "model_groups.json")).ToObject<Dictionary<string, ModelGroup>>()!;
        Families = JArray.Parse(File.ReadAllText(Path.Combine(root, "families.json"))).ToObject<List<TemplateInfo>>()!;
        var data = JsonData.Read(Path.Combine(root, "presets", "index.json"));
        if (data["schema_version"].Text() != "packstudio.preset-index/v4")
            throw new InvalidDataException("预设索引版本不受支持。");
        index = (JObject)data["presets"]!;
    }

    public Template Load(string id)
    {
        if (cache.TryGetValue(id, out var cached))
            return cached;
        var info = Families.Single(f => f.Id == id);
        var data = JsonData.Read(Path.Combine(root, "templates", id + ".json"));
        var presets = new List<ProjectDocument>();
        foreach (var p in index.Properties().Where(p => p.Value["family"].Text() == id))
        {
            var document = ProjectDocument.ReadCurrent(JsonData.CatalogEntry(Path.Combine(root, "presets"), p.Value));
            if (document.Name != p.Name || document.TemplateId != id)
                throw new InvalidDataException($"预设标识或版本无效：{p.Name}");
            presets.Add(document);
        }
        Func<FourLayerConfiguration>? loadFourLayer = id is "chip_array" or "pbga_wb"
            ? () => FourLayerConfiguration.Load(Path.Combine(root, "presets", id, "four_layer.json"), id) : null;
        var template = new Template(info, data, presets, loadFourLayer);
        foreach (var preset in presets) MaterialSelection.Resolve(template, preset.MaterialAssignments);
        return cache[id] = template;
    }

}
