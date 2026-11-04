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
}
