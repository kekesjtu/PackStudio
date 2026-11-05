using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static class ExposedPadInitializer
{
    public static void Apply(PackageDefinition definition, JObject values, JObject selection, JObject? configuration)
    {
        if (definition.Info.Id is not ("sop" or "pqfp") || !selection["package.exposed_pad"].Flag()) return;
        if (configuration == null) throw new InvalidDataException($"缺少 {definition.Info.Id} 露出焊盘创建配置。");
        foreach (var property in ((JObject)configuration["values"]!).Properties())
            values[property.Name] = property.Value.DeepClone();
        values["flag.downset"] = selection[configuration["flag_downset_source"].Text()]?.DeepClone() ?? JValue.CreateNull();
    }
}
