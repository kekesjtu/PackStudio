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
    readonly ConcurrentDictionary<string, FourLayerConfiguration> fourLayer = new();
    readonly ConcurrentDictionary<string, JObject> exposedPad = new();

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
        CheckDocument(data, "packstudio.definition/v3", id);
        if (data["keys"] is not JArray keys || data["materials"] is not JArray materials || data["steps"] is not JArray steps)
            throw new InvalidDataException($"{id} 参数定义缺少 keys、materials 或 steps。");
        CheckFields(keys);
        CheckFields(materials, "combobox");
        if (steps.Select(s => s["key"].Text()).Distinct().Count() != steps.Count)
            throw new InvalidDataException($"{id} 包含重复步骤。");
        foreach (var key in keys.Concat(materials).Where(k => k["step"] != null))
            if (!steps.Any(s => s["key"].Text() == key["step"].Text()) && !key["creation_option"].Flag() && key["type"].Text() != "footprint")
                throw new InvalidDataException($"字段 {key["key"]} 引用未知步骤 {key["step"]}。");
        var presets = new List<ProjectDocument>();
        foreach (var entry in index.Properties().Where(p => p.Value["family"].Text() == id))
        {
            var document = ProjectStore.ReadCurrent(JsonData.CatalogEntry(Path.Combine(root, "presets"), entry.Value));
            if (document.Name != entry.Name || document.TemplateId != id)
                throw new InvalidDataException($"预设标识无效：{entry.Name}");
            foreach (var field in keys.Where(f => !f["creation_only"].Flag() && f["type"].Text() != "footprint"))
                if (document.Values.Property(field["key"].Text()) == null)
                    throw new InvalidDataException($"预设 {entry.Name} 缺少参数 {field["key"]}。");
            presets.Add(document);
        }
        var definition = new PackageDefinition(info, data, presets);
        foreach (var preset in presets)
        {
            var issues = new List<ValidationIssue>();
            InputValidator.ValidateMaterials(preset, definition, Materials, issues);
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

    static void CheckDocument(JObject data, string version, string id)
    {
        if (data["schema_version"].Text() != version || data["template_id"].Text() != id)
            throw new InvalidDataException($"{id} 运行数据标识或版本无效。");
    }

    static void CheckFields(JArray fields, string defaultType = "")
    {
        if (fields.Select(f => f["key"].Text()).Distinct().Count() != fields.Count)
            throw new InvalidDataException("参数定义包含重复键。");
        foreach (var field in fields)
        {
            if (field["key"].Text().Length == 0 || field["type"].Text(defaultType).Length == 0)
                throw new InvalidDataException("参数定义缺少键或数据类型。");
            if (field["columns"] is JArray columns) CheckFields(columns);
            foreach (var option in field["options"] as JArray ?? [])
                if (option is not JObject record || record["value"] is not JValue ||
                    record["label"] is { Type: not JTokenType.String })
                    throw new InvalidDataException($"参数 {field["key"]} 的选项必须包含 value 和可选的 label。");
        }
    }
}
