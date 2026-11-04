using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public sealed class ProjectDocument
{
    public string SchemaVersion { get; set; } = "packstudio.project/v3";
    public string TemplateId { get; set; } = "";
    public string PresetId { get; set; } = "";
    public string Name { get; set; } = "";
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
        var draft = new CreationDraft(template, presetId ?? template.DefaultPreset);
        foreach (var p in options?.Properties() ?? []) draft.Set(p.Name, p.Value);
        return draft.Complete(name ?? template.Info.Name);
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
        var serializer = JsonSerializer.Create(new JsonSerializerSettings { MissingMemberHandling = MissingMemberHandling.Error });
        var document = data.ToObject<ProjectDocument>(serializer) ?? throw new InvalidDataException("方案文件为空。");
        if (!catalog.Families.Any(f => f.Id == document.TemplateId))
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
