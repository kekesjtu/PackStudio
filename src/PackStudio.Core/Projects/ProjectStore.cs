using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static class ProjectStore
{
    public static ProjectDocument Load(string path, RuntimeDataCatalog catalog)
    {
        if (new FileInfo(path).Length > 16 * 1024 * 1024)
            throw new InvalidDataException("方案文件超过 16 MB。");
        var document = ReadCurrent(ProjectMigration.Read(JsonData.Read(path), catalog));
        if (!catalog.Families.Any(f => f.Id == document.TemplateId))
            throw new InvalidDataException("未知封装类型。");
        return document;
    }

    public static ProjectDocument ReadCurrent(JObject data)
    {
        if (data["CustomMaterials"] is JArray records && records.Any(r => r is not JObject || r["Conductivity"] is not JObject ||
            r["ConductType"] is { Type: not JTokenType.Integer }))
            throw new InvalidDataException("自定义材料必须为材料对象，包含导热率对象和整数导热类型。");
        var serializer = JsonSerializer.Create(new JsonSerializerSettings { MissingMemberHandling = MissingMemberHandling.Error });
        var document = data.ToObject<ProjectDocument>(serializer) ?? throw new InvalidDataException("方案文件为空。");
        if (data["SchemaVersion"].Text() != ProjectDocument.CurrentVersion ||
            data["TemplateId"]?.Type != JTokenType.String || data["Name"]?.Type != JTokenType.String ||
            data["Values"] is not JObject || data["MaterialAssignments"] is not JObject assignments ||
            assignments.Properties().Any(p => p.Value.Type != JTokenType.String) || data["CustomMaterials"] is not JArray ||
            document.Values.Property("footprint.size") != null)
            throw new InvalidDataException("方案版本或数据结构无效。");
        return document;
    }

    public static void Save(ProjectDocument document, string path)
    {
        if (document.SchemaVersion != ProjectDocument.CurrentVersion || document.Values.Property("footprint.size") != null)
            throw new InvalidDataException("方案包含无效版本或预设字段。");
        string temp = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            File.WriteAllText(temp, JsonConvert.SerializeObject(document, Formatting.Indented));
            File.Move(temp, path, true);
        }
        finally
        {
            if (File.Exists(temp)) File.Delete(temp);
        }
    }
}
