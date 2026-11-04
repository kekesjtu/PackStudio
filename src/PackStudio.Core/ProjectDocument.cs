using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public sealed class ProjectDocument
{
    public const string CurrentVersion = "packstudio.project/v4";
    public string SchemaVersion { get; set; } = CurrentVersion;
    public string TemplateId { get; set; } = "";
    public string Name { get; set; } = "";
    public JObject Values { get; set; } = new();
    public Dictionary<string, string> MaterialAssignments { get; set; } = [];
    public List<Material> CustomMaterials { get; set; } = [];

    public ProjectDocument Clone() => new()
    {
        SchemaVersion = SchemaVersion, TemplateId = TemplateId, Name = Name,
        Values = (JObject)Values.DeepClone(),
        MaterialAssignments = new(MaterialAssignments), CustomMaterials = [.. CustomMaterials]
    };
    public static ProjectDocument Create(Template template, string? presetId = null, string? name = null, JObject? options = null)
    {
        string preset = presetId ?? template.DefaultPreset;
        return CreationDraft.Create(template, preset, name ?? template.Presets.FirstOrDefault(p => p.Name == preset)?.Name ?? template.Info.Name, options);
    }

    internal static void ValidateName(string name)
    {
        if (string.IsNullOrWhiteSpace(name) || name.Length > 160)
            throw new ArgumentException("方案名称需要 1–160 个字符。");
    }

    public static ProjectDocument Load(string path, PackageCatalog catalog)
    {
        if (new FileInfo(path).Length > 16 * 1024 * 1024)
            throw new InvalidDataException("方案文件超过 16 MB。");
        var data = ProjectMigration.Read(JsonData.Read(path), catalog);
        var document = ReadCurrent(data);
        if (!catalog.Families.Any(f => f.Id == document.TemplateId))
            throw new InvalidDataException("未知封装类型。");
        var template = catalog.Load(document.TemplateId);
        template.Validate(document.Values);
        MaterialSelection.Resolve(template, document.MaterialAssignments);
        return document;
    }

    internal static ProjectDocument ReadCurrent(JObject data)
    {
        var serializer = JsonSerializer.Create(new JsonSerializerSettings { MissingMemberHandling = MissingMemberHandling.Error });
        var document = data.ToObject<ProjectDocument>(serializer) ?? throw new InvalidDataException("方案文件为空。");
        if (data["SchemaVersion"].Text() != CurrentVersion || document.Values == null ||
            document.MaterialAssignments == null || document.CustomMaterials == null || document.Values.Property("footprint.size") != null)
            throw new InvalidDataException("方案版本或数据结构无效。");
        ValidateName(document.Name);
        return document;
    }

    public void Save(string path)
    {
        ValidateName(Name);
        if (SchemaVersion != CurrentVersion || Values.Property("footprint.size") != null)
            throw new InvalidDataException("方案包含无效版本或预设字段。");
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
