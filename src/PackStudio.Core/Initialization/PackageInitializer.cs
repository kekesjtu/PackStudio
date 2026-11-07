using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static class PackageInitializer
{
    public static ProjectDocument Create(PackageDefinition definition, string? presetId = null, string? name = null,
        JObject? overrides = null, FourLayerConfiguration? fourLayer = null, JObject? exposedPad = null)
    {
        string presetName = presetId ?? definition.DefaultPreset;
        var preset = definition.GetPreset(presetName);
        var values = (JObject)preset.Values.DeepClone();
        var selection = (JObject)values.DeepClone();
        Overlay(selection, overrides);
        if (definition.Info.Id is "chip_array" or "pbga_wb" && selection["substrate.layers"] is { Type: JTokenType.String } layers && layers.Value<string>() == "4-Layer")
            (fourLayer ?? throw new InvalidDataException($"缺少 {definition.Info.Id} 四层创建配置。")).Apply(values, presetName);
        ExposedPadInitializer.Apply(definition, values, selection, exposedPad);
        Overlay(values, overrides);
        MetalLayersInitializer.Apply(definition, values, overrides);
        values.Remove("footprint.size");
        return new ProjectDocument
        {
            TemplateId = definition.Info.Id,
            Name = name ?? preset.Name,
            Values = values,
            MaterialAssignments = new(preset.MaterialAssignments),
            CustomMaterials = [.. preset.CustomMaterials]
        };
    }

    static void Overlay(JObject target, JObject? source)
    {
        foreach (var property in source?.Properties() ?? [])
            target[property.Name] = property.Value.DeepClone();
    }
}
