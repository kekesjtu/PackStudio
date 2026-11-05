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
    readonly JObject commonRules;
    readonly JObject index;
    readonly ConcurrentDictionary<string, PackageDefinition> definitions = new();
    readonly ConcurrentDictionary<string, ValidationRules> rules = new();
    readonly ConcurrentDictionary<string, FourLayerConfiguration> fourLayer = new();
    readonly ConcurrentDictionary<string, JObject> exposedPad = new();

    public RuntimeDataCatalog(string root)
    {
        this.root = Path.GetFullPath(root);
        commonRules = JsonData.Read(Path.Combine(this.root, "validation", "common.json"));
        Materials = new MaterialCatalogReader().Read(this.root, new ValidationRules(commonRules));
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
            ui["fields"] is not JArray ||
            ui["steps"] is not JArray || ui["material_selections"] is not JArray)
            throw new InvalidDataException($"{id} 参数定义或 UI 模板结构无效。");
        CheckFields(fields);
        var presets = new List<ProjectDocument>();
        foreach (var entry in index.Properties().Where(p => p.Value["family"].Text() == id))
        {
            var document = ProjectStore.ReadCurrent(JsonData.CatalogEntry(Path.Combine(root, "presets"), entry.Value));
            if (document.Name != entry.Name || document.TemplateId != id)
                throw new InvalidDataException($"预设标识无效：{entry.Name}");
            foreach (var field in fields.Where(f => !f["creation_only"].Flag() && f["type"].Text() != "footprint"))
                if (document.Values.Property(field["key"].Text()) == null)
                    throw new InvalidDataException($"预设 {entry.Name} 缺少参数 {field["key"]}。");
            presets.Add(document);
        }
        var definition = new PackageDefinition(info, data, presets, new UiTemplate(ui, data));
        var materialRules = new ValidationRules(commonRules);
        foreach (var preset in presets)
        {
            var issues = new List<ValidationIssue>();
            InputValidator.ValidateMaterials(preset, definition, Materials, materialRules, issues);
            if (issues.Any(i => i.Severity == IssueSeverity.Error))
                throw new InvalidDataException($"预设 {preset.Name}：{string.Join(" ", issues.Select(i => i.Message))}");
        }
        return definition;
    }

    public FourLayerConfiguration LoadFourLayer(string id)
    {
        if (id is not ("chip_array" or "pbga_wb")) throw new InvalidDataException($"{id} 不使用四层创建配置。");
        return fourLayer.GetOrAdd(id, family => FourLayerConfiguration.Load(Path.Combine(root, "presets", family, "four_layer.json"), family));
    }

    public JObject LoadExposedPad(string id) => exposedPad.GetOrAdd(id, family =>
    {
        string directory = family switch
        {
            "sop" => "tsop_conv",
            "pqfp" => "pqfp",
            _ => throw new InvalidDataException($"{family} 不使用露出焊盘创建配置。")
        };
        var data = JsonData.Read(Path.Combine(root, "presets", directory, "exposed_pad.json"));
        if (data["schema_version"].Text() != "packstudio.exposed-pad/v1" || data["family"].Text() != family ||
            data.Properties().Any(p => p.Name is not ("schema_version" or "family" or "flag_downset_source" or "values")) ||
            data["flag_downset_source"]?.Type != JTokenType.String ||
            !Load(family).Fields.Any(f => f["key"].Text() == data["flag_downset_source"].Text() && f["type"].Text() == "number") ||
            data["values"] is not JObject values || values.Count != 2 ||
            values["thermal_land.enabled"]?.Type != JTokenType.Boolean ||
            values["thermal_land.thickness"]?.Type is not (JTokenType.Integer or JTokenType.Float) ||
            !double.IsFinite(values["thermal_land.thickness"]!.Value<double>()))
            throw new InvalidDataException($"{family} 露出焊盘创建配置版本、家族或字段无效。");
        return (JObject)data.DeepClone();
    });

    public ValidationRules LoadValidation(string id) => rules.GetOrAdd(id, family =>
    {
        var familyRules = JsonData.Read(Path.Combine(root, "validation", family + ".json"));
        CheckDocument(familyRules, "packstudio.validation/v1", family);
        var loaded = new ValidationRules(commonRules, familyRules);
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
