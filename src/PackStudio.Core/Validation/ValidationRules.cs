using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public sealed class ValidationRules
{
    static readonly HashSet<string> KnownChecks = ["solder_ball_pitch", "via_pitch", "via_plating", "metal_layers", "sop_lead_count", "array_layout", "overlap", "builtin", "relation", "prerequisite"];
    public JArray Fields { get; }
    public JArray Checks { get; }
    readonly JObject materialMessages;

    public ValidationRules(JObject common, JObject? family = null)
    {
        foreach (var data in new[] { common, family }.OfType<JObject>())
            if (data["schema_version"].Text() != "packstudio.validation/v1")
                throw new InvalidDataException("校验规则版本不受支持。");
        Fields = (JArray)(family?["fields"] ?? new JArray()).DeepClone();
        Checks = new JArray((common["checks"] as JArray ?? []).Concat(family?["checks"] as JArray ?? [])
            .Where(c => c["families"] is not JArray families || families.Any(f => f.Text() == family?["template_id"].Text()))
            .Select(c => c.DeepClone()));
        materialMessages = (JObject)(common["material_messages"] ?? new JObject()).DeepClone();
        var ids = new HashSet<string>();
        foreach (var check in Checks)
        {
            string id = check["id"].Text();
            string checker = check["check"].Text(), stage = check["stage"].Text();
            if (id.Length == 0 || !ids.Add(id) || !KnownChecks.Contains(checker) ||
                check["stage"].Text() is not ("input" or "model" or "generation") || check["severity"].Text() is not ("error" or "warning") ||
                string.IsNullOrWhiteSpace(check["message"].Text()))
                throw new InvalidDataException($"无效、重复或未知校验规则 {id}。");
            if (checker == "overlap" && stage != "model" || checker is "relation" or "solder_ball_pitch" or "via_pitch" or "via_plating" or "metal_layers" or "sop_lead_count" or "array_layout" && stage != "input")
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
            if (field["severity"] != null && field["severity"].Text() is not ("error" or "warning"))
                throw new InvalidDataException($"字段 {key} 的规则严重度无效。");
            foreach (string children in new[] { "fields", "columns" })
                if (field[children] is JArray nested)
                    CheckFields(nested, definition[children] as JArray ?? []);
        }
    }

    public bool Contains(string code) => Checks.Any(r => r["id"].Text() == code);

    public string MaterialMessage(string failure) => materialMessages[failure]?.Value<string>()
        ?? throw new InvalidDataException($"缺少材料诊断文本 {failure}。");

    public ValidationIssue Create(string code, ValidationStage stage, string[] paths, string[]? entities = null,
        string detail = "", string reason = "", JToken? field = null)
    {
        var rule = Checks.FirstOrDefault(r => r["id"].Text() == code)
            ?? throw new InvalidDataException($"缺少校验声明 {code}。");
        if (rule["stage"].Text() != stage.ToString().ToLowerInvariant())
            throw new InvalidDataException($"校验声明 {code} 阶段不匹配。");
        string severity = field?["severity"].Text(rule["severity"].Text()) ?? rule["severity"].Text();
        string message = field?["messages"]?[code].Text(rule["message"].Text()) ?? rule["message"].Text();
        return new(code, severity == "warning" ? IssueSeverity.Warning : IssueSeverity.Error, stage,
            message.Replace("{path}", paths.FirstOrDefault() ?? "").Replace("{entity}", entities?.FirstOrDefault() ?? "")
                .Replace("{detail}", detail).Replace("{reason}", reason), paths, entities ?? []);
    }
}
