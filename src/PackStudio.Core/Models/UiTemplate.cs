using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public sealed class UiTemplate
{
    public JObject Data { get; }
    public JArray Fields { get; }
    public JArray MaterialSelections { get; }
    public JArray Steps => (JArray)Data["steps"]!;

    public UiTemplate(JObject data, JObject definition)
    {
        Data = data;
        Fields = Merge((JArray)definition["fields"]!, (JArray)data["fields"]!);
        MaterialSelections = Merge((JArray)definition["material_selections"]!, (JArray)data["material_selections"]!, "group_id");
    }

    static JArray Merge(JArray definitions, JArray presentation, string identity = "key")
    {
        var result = new JArray();
        foreach (var source in presentation)
        {
            string key = source[identity].Text();
            var semantic = definitions.SingleOrDefault(f => f[identity].Text() == key)
                ?? throw new InvalidDataException($"UI 模板引用未知字段 {key}。");
            var field = (JObject)semantic.DeepClone();
            foreach (var property in ((JObject)source).Properties())
                if (property.Name is not ("fields" or "columns")) field[property.Name] = property.Value.DeepClone();
            if (source["fields"] is JArray children)
                field["fields"] = Merge((JArray)semantic["fields"]!, children);
            if (source["columns"] is JArray columns)
                field["columns"] = Merge((JArray)semantic["columns"]!, columns);
            result.Add(field);
        }
        return result;
    }
}
