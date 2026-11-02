using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

// 旧文件与研究请求的格式转换集中在输入边界，生成和编辑只使用当前方案结构。
internal static class ProjectInput
{
    internal static void MergeLayout(JObject values, JObject? layout)
    {
        if (layout == null) return;
        foreach (var property in layout.Properties())
            values["bga." + property.Name] = property.Value.DeepClone();
    }

    internal static void NormalizeTables(JObject values)
    {
        foreach (string key in new[] { "metal.layers", "upper.layers", "lower.layers" })
            if (values[key]?.Type == JTokenType.String)
                values[key] = JArray.Parse(values[key]!.Value<string>()!);
    }

    internal static void Upgrade(JObject data)
    {
        var values = (JObject?)data["Values"] ?? new JObject();
        MergeLayout(values, data["Bga"] as JObject);
        NormalizeTables(values);
        data["Values"] = values;
        data["MaterialAssignments"] = data["Assignments"]?.DeepClone() ?? new JObject();
        data.Remove("Bga");
        data.Remove("Assignments");
        data["SchemaVersion"] = "packstudio.project/v2";
    }
}
