using System.Collections.Concurrent;
using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public sealed class RuntimeDataCatalog
{
    public IReadOnlyList<TemplateInfo> Families { get; }
    public TemplateInfo DefaultFamily => Families.Single(f => f.IsDefault);
    public MaterialCatalog Materials { get; }
    public IReadOnlyDictionary<string, ModelGroup> Groups { get; }
    readonly string root;
    readonly JObject index;
    readonly ConcurrentDictionary<string, PackageDefinition> definitions = new();
    readonly ConcurrentDictionary<string, ValidationRules> rules = new();
    readonly ConcurrentDictionary<string, FourLayerConfiguration> fourLayer = new();

    public RuntimeDataCatalog(string root)
    {
        this.root = Path.GetFullPath(root);
        Materials = new MaterialCatalogReader().Read(this.root);
        Groups = JsonData.Read(Path.Combine(this.root, "model_groups.json")).ToObject<Dictionary<string, ModelGroup>>()!;
        Families = JArray.Parse(File.ReadAllText(Path.Combine(this.root, "families.json"))).ToObject<List<TemplateInfo>>()!;
        var data = JsonData.Read(Path.Combine(this.root, "presets", "index.json"));
        if (data["schema_version"].Text() != "packstudio.preset-index/v4")
            throw new InvalidDataException("预设索引版本不受支持。");
        index = data["presets"] as JObject ?? throw new InvalidDataException("预设索引结构无效。");
    }

    public PackageDefinition Load(string id) => definitions.GetOrAdd(id, LoadDefinition);

    PackageDefinition LoadDefinition(string id)
    {
        var info = Families.SingleOrDefault(f => f.Id == id) ?? throw new InvalidDataException($"未知封装类型 {id}。");
        var data = JsonData.Read(Path.Combine(root, "definitions", id + ".json"));
        var ui = JsonData.Read(Path.Combine(root, "templates", id + ".json"));
        CheckDocument(data, "packstudio.definition/v1", id);
        CheckDocument(ui, "packstudio.ui-template/v1", id);
        if (data["fields"] is not JArray fields || data["material_selections"] is not JArray ||
            data["baseline_materials"] is not JArray baseline || ui["fields"] is not JArray ||
            ui["steps"] is not JArray || ui["material_selections"] is not JArray)
            throw new InvalidDataException($"{id} 参数定义或 UI 模板结构无效。");
        CheckFields(fields);
        var presets = new List<ProjectDocument>();
        foreach (var entry in index.Properties().Where(p => p.Value["family"].Text() == id))
        {
            var document = ProjectStore.ReadCurrent(JsonData.CatalogEntry(Path.Combine(root, "presets"), entry.Value));
            if (document.Name != entry.Name || document.TemplateId != id)
                throw new InvalidDataException($"预设标识无效：{entry.Name}");
            foreach (var field in fields.Where(f => !f["creation_only"].Flag() && f["type"].Text() is not ("footprint" or "derived")))
                if (document.Values.Property(field["key"].Text()) == null)
                    throw new InvalidDataException($"预设 {entry.Name} 缺少参数 {field["key"]}。");
            presets.Add(document);
        }
        var baselineMaterials = baseline.Select(MaterialCatalogReader.Parse).ToArray();
        foreach (var material in baselineMaterials)
        {
            string[] errors = FieldRules.MaterialErrors(material).ToArray();
            if (errors.Length > 0) throw new InvalidDataException($"基线材料 {material.Id}：{string.Join(" ", errors)}");
        }
        var definition = new PackageDefinition(info, data, presets, new UiTemplate(ui, data), baselineMaterials);
        foreach (var preset in presets) MaterialSelection.Resolve(definition, preset.MaterialAssignments);
        return definition;
    }

    public FourLayerConfiguration LoadFourLayer(string id)
    {
        if (id is not ("chip_array" or "pbga_wb")) throw new InvalidDataException($"{id} 不使用四层创建配置。");
        return fourLayer.GetOrAdd(id, family => FourLayerConfiguration.Load(Path.Combine(root, "presets", family, "four_layer.json"), family));
    }

    public ValidationRules LoadValidation(string id) => rules.GetOrAdd(id, family =>
    {
        var common = JsonData.Read(Path.Combine(root, "validation", "common.json"));
        var familyRules = JsonData.Read(Path.Combine(root, "validation", family + ".json"));
        CheckDocument(familyRules, "packstudio.validation/v1", family);
        var loaded = new ValidationRules(common, familyRules);
        loaded.CheckReferences(Load(family));
        return loaded;
    });

    static void CheckDocument(JObject data, string version, string id)
    {
        if (data["schema_version"].Text() != version || data["template_id"].Text() != id)
            throw new InvalidDataException($"{id} 运行数据标识或版本无效。");
    }

    static void CheckFields(JArray fields)
    {
        if (fields.Select(f => f["key"].Text()).Distinct().Count() != fields.Count)
            throw new InvalidDataException("参数定义包含重复键。");
        foreach (var field in fields)
        {
            if (field["key"].Text().Length == 0 || field["type"].Text().Length == 0)
                throw new InvalidDataException("参数定义缺少键或数据类型。");
            if (field["type"].Text() == "object")
            {
                if (field["fields"] is not JArray children || field["default"] is not JObject)
                    throw new InvalidDataException($"对象参数 {field["key"]} 缺少子字段或基线。");
                CheckFields(children);
            }
        }
    }
}
