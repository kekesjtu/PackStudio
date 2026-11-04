using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

/// <summary>Versioned file-boundary migration; never reinitializes saved geometry.</summary>
static class ProjectMigration
{
    public static JObject Read(JObject source, RuntimeDataCatalog catalog)
    {
        string version = source["SchemaVersion"].Text();
        if (version is not (ProjectDocument.CurrentVersion or "packstudio.project/v2" or "packstudio.project/v3"))
            throw new InvalidDataException("方案版本不受支持。");
        var data = (JObject)source.DeepClone();
        MapLegacyMaterials(data);
        if (version == ProjectDocument.CurrentVersion) return data;
        var template = catalog.Load(data["TemplateId"].Text());
        var values = (JObject)data["Values"]!;
        if (version == "packstudio.project/v2") MigrateValues(template, values);
        string presetName = data["PresetId"].Text(values["footprint.size"].Text());
        var preset = template.Presets.FirstOrDefault(p => p.Name == presetName);
        var materials = preset == null ? MaterialSelection.Defaults(template) : new(preset.MaterialAssignments);
        foreach (var property in (data["MaterialAssignments"] as JObject ?? new()).Properties())
            materials[property.Name] = property.Value.Text();
        data["MaterialAssignments"] = JObject.FromObject(materials);
        data.Remove("PresetId");
        values.Remove("footprint.size");
        data["SchemaVersion"] = ProjectDocument.CurrentVersion;
        return data;
    }

    static void MapLegacyMaterials(JObject data)
    {
        foreach (var material in (data["CustomMaterials"] as JArray ?? []).OfType<JObject>())
        {
            if (material.Property("ConductType") != null) continue;
            if (material["Conductivity"] is not JObject conductivity) continue;
            bool isotropic = JToken.DeepEquals(conductivity["X"], conductivity["Y"]) &&
                JToken.DeepEquals(conductivity["Y"], conductivity["Z"]);
            material["ConductType"] = isotropic && material["ConductivityCoefficient"]?.Type is JTokenType.Integer or JTokenType.Float ? 1 : isotropic ? 0 : 2;
        }
    }

    static void MigrateValues(PackageDefinition template, JObject values)
    {
        var legacy = values.Property("bga.via_configuration");
        if (legacy != null)
        {
            if (template.Fields.Any(f => f["key"].Text() == "vias.configuration")) values["vias.configuration"] = legacy.Value.DeepClone();
            legacy.Remove();
        }
        foreach (var field in template.Fields)
        {
            string key = field["key"].Text();
            if (values.Property(key) == null || field["type"].Text() == "object" && values[key]?.Type == JTokenType.Null)
                values[key] = field["default"]?.DeepClone() ?? JValue.CreateNull();
            if (field["default"] is JObject defaults && values[key] is JObject nested)
                foreach (var property in defaults.Properties())
                    if (nested.Property(property.Name) == null) nested[property.Name] = property.Value.DeepClone();
        }
    }
}
