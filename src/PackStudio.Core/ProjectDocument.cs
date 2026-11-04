using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public sealed class ProjectDocument
{
    public string SchemaVersion { get; set; } = "packstudio.project/v2";
    public string TemplateId { get; set; } = "bare_die";
    public string PresetId { get; set; } = "";
    public string Name { get; set; } = "Bare Die";
    public JObject Values { get; set; } = new();
    public Dictionary<string, string> MaterialAssignments { get; set; } = [];
    public List<Material> CustomMaterials { get; set; } = [];

    public ProjectDocument Clone() => new()
    {
        SchemaVersion = SchemaVersion, TemplateId = TemplateId, PresetId = PresetId, Name = Name,
        Values = (JObject)Values.DeepClone(),
        MaterialAssignments = new(MaterialAssignments), CustomMaterials = [.. CustomMaterials]
    };
    public static ProjectDocument Create(Template template, string? presetId = null, string? name = null, JObject? options = null)
    {
        string preset = presetId ?? template.DefaultPreset;
        return new() { TemplateId = template.Info.Id, PresetId = preset, Name = name ?? template.Info.Name, Values = ParameterRules.Prepare(template, template.Defaults(preset, options), options) };
    }

    public ProjectDocument CompleteCreation(Template template, string name)
    {
        var result = Clone();
        result.Name = name.Trim();
        ValidateName(result.Name);
        result.Values = ParameterRules.Prepare(template, result.Values);
        foreach (var field in template.CreationFields.Where(f => JsonData.Matches(f["visible_when"] as JObject, result.Values) &&
            f["control"].Text() is "number" or "integer" or "integer_spinbox"))
            if (result.Values[field["key"].Text()]?.Type is null or JTokenType.Null)
                throw new ArgumentException($"请填写{field["label"]}。");
        return result;
    }

    internal static void ValidateName(string name)
    {
        if (string.IsNullOrWhiteSpace(name) || name.Length > 160)
            throw new ArgumentException("方案名称需要 1–160 个字符。");
    }

    public static ProjectDocument Load(string path)
    {
        if (new FileInfo(path).Length > 16 * 1024 * 1024)
            throw new InvalidDataException("方案文件超过 16 MB。");
        var data = JsonData.Read(path);
        if (data["SchemaVersion"].Text() != "packstudio.project/v2")
            throw new InvalidDataException("方案版本不受支持。");
        var serializer = JsonSerializer.Create(new JsonSerializerSettings { MissingMemberHandling = MissingMemberHandling.Error });
        var document = data.ToObject<ProjectDocument>(serializer) ?? throw new InvalidDataException("方案文件为空。");
        if (!PackageCatalog.Families.Any(f => f.Id == document.TemplateId))
            throw new InvalidDataException("未知封装类型。");
        return document;
    }

    public void Save(string path)
    {
        string temp = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            File.WriteAllText(temp, JsonConvert.SerializeObject(this, Formatting.Indented));
            File.Move(temp, path, true);
        }
        finally
        {
            if (File.Exists(temp))
                File.Delete(temp);
        }
    }
}
