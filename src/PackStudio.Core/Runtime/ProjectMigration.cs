using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

/// <summary>Versioned file-boundary migration; never reinitializes saved geometry.</summary>
static class ProjectMigration
{
    public static JObject Read(JObject source, PackageCatalog catalog)
    {
        if (source["SchemaVersion"].Text() == "packstudio.project/v3") return source;
        if (source["SchemaVersion"].Text() != "packstudio.project/v2")
            throw new InvalidDataException("方案版本不受支持。");
        var data = (JObject)source.DeepClone();
        var template = catalog.Load(data["TemplateId"].Text());
        var values = (JObject)data["Values"]!;
        var legacy = values.Property("bga.via_configuration");
        if (legacy != null)
        {
            if (template.Fields.Any(f => f["key"].Text() == "vias.configuration")) values["vias.configuration"] = legacy.Value.DeepClone();
            legacy.Remove();
        }
        foreach (var field in template.Fields)
        {
            string key = field["key"].Text();
            if (values.Property(key) == null || field["control"].Text() == "object" && values[key]?.Type == JTokenType.Null)
                values[key] = field["default"]?.DeepClone() ?? JValue.CreateNull();
            if (field["default"] is JObject defaults && values[key] is JObject nested)
                foreach (var property in defaults.Properties())
                    if (nested.Property(property.Name) == null) nested[property.Name] = property.Value.DeepClone();
        }
        data["SchemaVersion"] = "packstudio.project/v3";
        return data;
    }
}
