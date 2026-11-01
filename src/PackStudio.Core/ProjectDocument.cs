using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace PackStudio.Core;
public sealed class ProjectDocument
{
    public string SchemaVersion { get; set; } = "packstudio.project/v1";
    public string TemplateId { get; set; } = "bare_die";
    public string PresetId { get; set; } = "";
    public string Name { get; set; } = "Bare Die";
    public JObject Values { get; set; } = new();
    public JObject Bga { get; set; } = new();
    public Dictionary<string, string> Assignments { get; set; } = [];
    public List<Material> CustomMaterials { get; set; } = [];

    public ProjectDocument Clone() => JsonConvert.DeserializeObject<ProjectDocument>(JsonConvert.SerializeObject(this))!;
    public static ProjectDocument Load(string path)
    {
        if (new FileInfo(path).Length > 16 * 1024 * 1024)
            throw new InvalidDataException("方案文件超过 16 MB。");
        var document = JsonConvert.DeserializeObject<ProjectDocument>(File.ReadAllText(path)) ?? throw new InvalidDataException("方案文件为空。");
        if (document.SchemaVersion != "packstudio.project/v1")
            throw new InvalidDataException("方案版本不受支持。");
        if (!PackageCatalog.Families.Any(f => f.Id == document.TemplateId))
            throw new InvalidDataException("未知封装类型。");
        NormalizeTables(document.Values);
        return document;
    }

    // v1 方案与归档请求的字符串层表只在输入边界转换，内部及保存结果统一使用数组。
    internal static void NormalizeTables(JObject values)
    {
        foreach (string key in new[] { "metal.layers", "upper.layers", "lower.layers" })
            if (values[key]?.Type == JTokenType.String)
                values[key] = JArray.Parse(values[key]!.Value<string>()!);
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
