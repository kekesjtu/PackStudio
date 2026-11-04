using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public sealed class ValidationRules
{
    static readonly HashSet<string> KnownChecks = ["solder_ball_pitch", "via_dimensions", "metal_layers", "sop_lead_count", "array_layout", "overlap"];
    public JArray Fields { get; }
    public JArray Checks { get; }

    public ValidationRules(JObject common, JObject? family = null)
    {
        foreach (var data in new[] { common, family }.OfType<JObject>())
            if (data["schema_version"].Text() != "packstudio.validation/v1")
                throw new InvalidDataException("校验规则版本不受支持。");
        Fields = (JArray)(family?["fields"] ?? new JArray()).DeepClone();
        Checks = new JArray((common["checks"] as JArray ?? []).Concat(family?["checks"] as JArray ?? []).Select(c => c.DeepClone()));
        var ids = new HashSet<string>();
        foreach (var check in Checks)
        {
            string id = check["id"].Text();
            string checker = check["check"].Text(), stage = check["stage"].Text();
            if (id.Length == 0 || !ids.Add(id) || !KnownChecks.Contains(checker) ||
                check["stage"].Text() is not ("input" or "model") || check["severity"].Text() is not ("error" or "warning"))
                throw new InvalidDataException($"无效、重复或未知校验规则 {id}。");
            if ((checker == "overlap") != (stage == "model"))
                throw new InvalidDataException($"校验规则 {id} 的阶段与检查器不匹配。");
        }
    }

    public void CheckReferences(PackageDefinition definition)
    {
        var keys = definition.Fields.Select(f => f["key"].Text()).ToHashSet();
        CheckFields(Fields, definition.Fields);
        foreach (var check in Checks)
            foreach (var parameter in check["parameters"] as JArray ?? [])
                if (!keys.Contains(parameter.Text())) throw new InvalidDataException($"校验规则 {check["id"]} 引用未知参数 {parameter}。");
    }

    static void CheckFields(JArray rules, JArray definitions)
    {
        var keys = new HashSet<string>();
        foreach (var field in rules)
        {
            string key = field["key"].Text();
            var definition = definitions.FirstOrDefault(f => f["key"].Text() == key);
            if (definition == null || !keys.Add(key)) throw new InvalidDataException($"校验规则引用未知或重复参数 {key}。");
            foreach (string children in new[] { "fields", "columns" })
                if (field[children] is JArray nested)
                    CheckFields(nested, definition[children] as JArray ?? []);
        }
    }

    public ValidationIssue Issue(JToken rule, ValidationStage stage, string fallbackMessage, string[] paths, string[]? entities = null)
        => new(rule["id"].Text(), rule["severity"].Text() == "warning" ? IssueSeverity.Warning : IssueSeverity.Error,
            stage, rule["message"].Text(fallbackMessage), paths, entities ?? []);
}
