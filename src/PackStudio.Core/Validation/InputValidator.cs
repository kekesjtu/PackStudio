using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static class InputValidator
{
    public static IReadOnlyList<ValidationIssue> Validate(ProjectDocument document, PackageDefinition definition, MaterialCatalog materials)
    {
        var issues = new List<ValidationIssue>();
        if (string.IsNullOrWhiteSpace(document.Name) || document.Name.Length > 160)
            issues.Add(ValidationIssue.Error("input.name", ValidationStage.Input, "设计名称不能为空且最多 160 个字符。", "Name"));
        if (document.TemplateId != definition.Info.Id)
        {
            issues.Add(ValidationIssue.Error("input.template", ValidationStage.Input, "方案与封装定义不匹配。", "TemplateId"));
            return issues.AsReadOnly();
        }
        ValidateFields(path => definition.ParameterDisplayName(path, document.Values), definition.Fields, document.Values, "", issues);
        ValidateMaterials(document, definition, materials, issues);
        var checks = new InputChecks(definition, document.Values, issues);
        switch (document.TemplateId)
        {
            case "bare_die": BareDieInputRules.Validate(checks); break;
            case "cbga_fc": CbgaFcInputRules.Validate(checks); break;
            case "pbga_fc": PbgaFcInputRules.Validate(checks); break;
            case "pbga_wb": PbgaWbInputRules.Validate(checks); break;
            case "chip_array": ChipArrayInputRules.Validate(checks); break;
            case "qfn": QfnInputRules.Validate(checks); break;
            case "pqfp": PqfpInputRules.Validate(checks); break;
            case "sop": SopInputRules.Validate(checks); break;
        }
        return issues.AsReadOnly();
    }

    static bool Active(JToken field, JObject values)
    {
        bool Numeric(string key) => double.IsFinite(InputChecks.Number(values[key]));
        if ((field["requires_numeric"] as JArray ?? []).Any(k => !Numeric(k.Text()))) return false;
        if ((field["requires_positive"] as JArray ?? []).Any(k => !Numeric(k.Text()) || values[k.Text()]!.Value<double>() <= 0)) return false;
        if (field["inactive_when"] is JObject inactive && JsonData.Matches(inactive, values)) return false;
        if (field["active_when"] is not JObject conditions) return true;
        if (conditions["all"] is JArray all) return all.All(c => JsonData.Matches(c as JObject, values));
        return JsonData.Matches(conditions, values);
    }

    static void ValidateFields(Func<string, string> displayName, JArray fields, JObject values, string prefix, List<ValidationIssue> issues)
    {
        foreach (var field in fields)
        {
            string key = field["key"].Text(), path = prefix + key;
            if (field["creation_only"].Flag() || !Active(field, values)) continue;
            string type = field["type"].Text();
            var value = values[key];
            void Error(string code, string message) => issues.Add(ValidationIssue.Error(code, ValidationStage.Input, $"{displayName(path)}：{message}", path));
            if (value?.Type is null or JTokenType.Null)
            {
                if (field["required"]?.Value<bool>() != false && type is ("number" or "integer" or "checkbox" or "table" or "removal_matrix" or "combobox" or "text"))
                    Error("input.required", "需要填写参数。");
                continue;
            }
            if (type is "number" or "integer")
            {
                if (value.Type is not (JTokenType.Float or JTokenType.Integer))
                { Error("input.type.number", "必须为数值。"); continue; }
                double number = value.Value<double>();
                if (!double.IsFinite(number) || type == "integer" && (number != Math.Truncate(number) || number < int.MinValue || number > int.MaxValue))
                { Error("input.number", "必须为有限数值，整数参数须为有效整数。"); continue; }
                if (field["minimum"]?.Type is JTokenType.Integer or JTokenType.Float && number < field["minimum"]!.Value<double>() ||
                    field["exclusive_minimum"]?.Type is JTokenType.Integer or JTokenType.Float && number <= field["exclusive_minimum"]!.Value<double>() ||
                    field["maximum"]?.Type is JTokenType.Integer or JTokenType.Float && number > field["maximum"]!.Value<double>())
                    Error("input.range", "超出允许范围。");
            }
            else if (type == "checkbox" && value.Type != JTokenType.Boolean)
            { Error("input.type.boolean", "必须为布尔值。"); continue; }
            else if (type is "combobox" or "text" && value.Type != JTokenType.String)
            { Error("input.type.string", "必须为字符串选项。"); continue; }
            else if (type is "table" or "removal_matrix")
            {
                if (value is not JArray rows) Error("input.type.array", "必须为数组。");
                else ValidateRows(displayName, field, rows, path, issues);
            }
            if (PackageDefinition.OptionValues(field) is { Count: > 0 } options && !options.Any(o => JToken.DeepEquals(o, value)))
                Error("input.option", "选项无效。");
        }
    }

    static void ValidateRows(Func<string, string> displayName, JToken field, JArray rows, string path, List<ValidationIssue> issues)
    {
        if (field["columns"] is not JArray columns) return;
        if (field["min_rows"] is JToken min && rows.Count < min.Value<int>() || field["max_rows"] is JToken max && rows.Count > max.Value<int>())
            issues.Add(ValidationIssue.Error("input.rows", ValidationStage.Input, $"{displayName(path)}行数超出允许范围。", path));
        for (int i = 0; i < rows.Count; i++)
        {
            if (rows[i] is not JObject row)
            { issues.Add(ValidationIssue.Error("input.row", ValidationStage.Input, $"{displayName($"{path}[{i}]")}：必须为对象。", $"{path}[{i}]")); continue; }
            if (row.Properties().Any(p => !columns.Any(c => c["key"].Text() == p.Name)))
                issues.Add(ValidationIssue.Error("input.row.columns", ValidationStage.Input, $"{displayName($"{path}[{i}]")}包含未知列。", $"{path}[{i}]"));
            ValidateFields(displayName, columns, row, $"{path}[{i}].", issues);
        }
    }

    internal static void ValidateMaterials(ProjectDocument document, PackageDefinition definition, MaterialCatalog catalog, List<ValidationIssue> issues)
    {
        var materials = catalog.Items.ToDictionary(p => p.Key, p => p.Value);
        foreach (var material in document.CustomMaterials)
        {
            materials[material.Id] = material;
            foreach (string error in FieldRules.MaterialErrors(material))
                issues.Add(ValidationIssue.Error("input.material", ValidationStage.Input, $"材料 {material.Name}：{error}", "CustomMaterials." + material.Id));
        }
        foreach (var duplicate in document.CustomMaterials.GroupBy(m => m.Id).Where(g => g.Count() > 1))
            issues.Add(ValidationIssue.Error("input.material.duplicate", ValidationStage.Input, $"重复自定义材料 {duplicate.First().Name}。", "CustomMaterials." + duplicate.Key));
        foreach (var selection in definition.MaterialSelections)
        {
            string group = selection["key"].Text(), path = "MaterialAssignments." + group;
            string label = selection["label"].Text("材料");
            if (!document.MaterialAssignments.TryGetValue(group, out var id))
                issues.Add(ValidationIssue.Error("input.material.missing", ValidationStage.Input, $"{label}：请选择材料。", path));
            else if (!MaterialSelection.Allows(selection, id) || id.Length > 0 && !materials.ContainsKey(id))
                issues.Add(ValidationIssue.Error("input.material.reference", ValidationStage.Input, $"{label}：所选材料不存在或不适用于此处。", path));
        }
        foreach (string group in document.MaterialAssignments.Keys.Except(definition.MaterialSelections.Select(s => s["key"].Text())))
            issues.Add(ValidationIssue.Error("input.material.group", ValidationStage.Input, "存在未定义的材料选择。", "MaterialAssignments." + group));
    }
}
