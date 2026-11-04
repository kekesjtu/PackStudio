using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

/// <summary>Family-local four-layer settings, read only on an explicit creation choice.</summary>
public sealed class FourLayerConfiguration
{
    [JsonProperty("schema_version")]
    public string SchemaVersion { get; set; } = "";
    [JsonProperty("family")]
    public string Family { get; set; } = "";
    [JsonProperty("values")]
    public JObject Values { get; set; } = new();
    [JsonProperty("preset_values")]
    public Dictionary<string, JObject> PresetValues { get; set; } = [];

    public static FourLayerConfiguration Load(string path, string family)
    {
        var serializer = JsonSerializer.Create(new JsonSerializerSettings { MissingMemberHandling = MissingMemberHandling.Error });
        var config = JsonData.Read(path).ToObject<FourLayerConfiguration>(serializer)
            ?? throw new InvalidDataException($"四层配置为空：{path}");
        if (config.SchemaVersion != "packstudio.four-layer/v1" || config.Family != family ||
            config.Values == null || config.PresetValues == null ||
            config.Values["metal.layers"] is not JArray { Count: 4 } || config.Values["substrate.layers"].Text() != "4-Layer")
            throw new InvalidDataException($"四层配置版本、家族或层栈无效：{path}");
        foreach (var field in config.Values.Properties())
            if (field.Name is not ("metal.layers" or "substrate.layers" or "substrate.thickness" or "vias.rows" or "vias.columns"))
                throw new InvalidDataException($"未知四层配置字段 {field.Name}。");
        foreach (var preset in config.PresetValues)
            if (preset.Value == null || preset.Value.Properties().Any(p => p.Name is not ("spreader.length" or "spreader.width")))
                throw new InvalidDataException($"四层配置 {preset.Key} 的散热片字段无效。");
        return config;
    }

    public void Apply(JObject target, string presetName)
    {
        foreach (var property in Values.Properties()) target[property.Name] = property.Value.DeepClone();
        if (PresetValues.TryGetValue(presetName, out var values))
            foreach (var property in values.Properties()) target[property.Name] = property.Value.DeepClone();
    }
}
