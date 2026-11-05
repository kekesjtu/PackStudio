using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static class PackageInitializer
{
    public static ProjectDocument Create(PackageDefinition definition, string? presetId = null, string? name = null,
        JObject? overrides = null, FourLayerConfiguration? fourLayer = null, JObject? exposedPad = null)
    {
        string presetName = presetId ?? definition.DefaultPreset;
        var preset = definition.Presets.FirstOrDefault(p => p.Name == presetName);
        var values = definition.DisplayDefaults(presetName);
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
            Name = name ?? preset?.Name ?? definition.Info.Name,
            Values = values,
            MaterialAssignments = preset == null ? MaterialSelection.Defaults(definition) : new(preset.MaterialAssignments),
            CustomMaterials = preset == null ? [] : [.. preset.CustomMaterials]
        };
    }

    static void Overlay(JObject target, JObject? source)
    {
        foreach (var property in source?.Properties() ?? [])
        {
            string[] path = property.Name.Split('/');
            var scope = target;
            foreach (string segment in path[..^1])
            {
                if (scope[segment] is not JObject nested) scope[segment] = nested = new JObject();
                scope = nested;
            }
            scope[path[^1]] = property.Value.DeepClone();
        }
    }
}
