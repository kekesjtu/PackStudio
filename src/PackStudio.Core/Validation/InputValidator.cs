using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static class InputValidator
{
    public static IReadOnlyList<ValidationIssue> Validate(ProjectDocument document, PackageDefinition definition, MaterialCatalog materials, ValidationRules rules)
    {
        var issues = new List<ValidationIssue>();
        void Error(string code, string message, params string[] paths) => issues.Add(ValidationIssue.Error(code, ValidationStage.Input, message, paths));
        if (string.IsNullOrWhiteSpace(document.Name) || document.Name.Length > 160)
            Error("input.name", "设计名称不能为空且最多 160 个字符。", "Name");
        if (document.TemplateId != definition.Info.Id) Error("input.template", "方案与封装定义不匹配。", "TemplateId");
        ValidateFields(rules.Fields, definition.Fields, document.Values, "", document.TemplateId, issues);
        ValidateMaterials(document, definition, materials, issues);
        ValidateRelations(document, rules, issues);
        issues.AddRange(PackageInputChecks.Validate(document, issues));
        return issues.AsReadOnly();
    }

    static bool Active(JToken field, JObject values)
    {
        if (field["active_when"] is not JObject conditions) return true;
        if (conditions["all"] is JArray all) return all.All(c => JsonData.Matches(c as JObject, values));
        return JsonData.Matches(conditions, values);
    }

    static bool Used(string templateId, string key, JObject values)
    {
        bool Numeric(string parameter) => values[parameter]?.Type is JTokenType.Integer or JTokenType.Float && double.IsFinite(values[parameter]!.Value<double>());
        if (templateId == "pbga_fc" && key is "upper.diameter" or "upper.plating" or "upper.filled" or "lower.diameter" or "lower.plating" or "lower.filled")
            return Numeric(key.Split('.')[0] + ".count");
        if (templateId == "qfn" && key == "leads.pitch_y")
            return Numeric("leads.count_y") && values["leads.count_y"]!.Value<double>() > 0;
        return templateId != "chip_array" || key is not ("vias.offset_x" or "vias.offset_y") ||
            values["vias.modeling"] is { Type: JTokenType.String } mode && mode.Value<string>() != "approximate";
    }

    static void ValidateFields(JArray fields, JArray definitions, JObject values, string prefix, string templateId, List<ValidationIssue> issues)
    {
        foreach (var field in fields)
        {
            string key = field["key"].Text(), path = prefix + key;
            var definition = definitions.FirstOrDefault(f => f["key"].Text() == key);
            if (definition == null) throw new InvalidDataException($"校验规则引用未知参数 {path}。");
            if (definition["creation_only"].Flag() || !Active(field, values) || !Used(templateId, key, values)) continue;
            string type = definition["type"].Text();
            var value = values[key];
            void Error(string code, string message) => issues.Add(ValidationIssue.Error(code, ValidationStage.Input, $"{path}：{message}", path));
            if (value?.Type is null or JTokenType.Null)
            {
                if (field["required"]?.Value<bool>() != false && type is ("number" or "integer" or "integer_spinbox" or "checkbox" or "object" or "table" or "removal_matrix" or "combobox" or "select" or "text"))
                    Error("input.required", "需要填写参数。");
                continue;
            }
            if (type is "number" or "integer" or "integer_spinbox")
            {
                if (value.Type is not (JTokenType.Float or JTokenType.Integer)) { Error("input.type", "必须为数值。"); continue; }
                double number = value.Value<double>();
                if (!double.IsFinite(number) || type.StartsWith("integer") && (number != Math.Truncate(number) || number < int.MinValue || number > int.MaxValue))
                { Error("input.number", "必须为有限数值，整数参数须为有效整数。"); continue; }
                double minimum = field["minimum"]?.Type is JTokenType.Integer or JTokenType.Float ? field["minimum"]!.Value<double>() : double.NegativeInfinity;
                if (number < minimum || field["maximum"]?.Type is JTokenType.Integer or JTokenType.Float && number > field["maximum"]!.Value<double>())
                    Error("input.range", "超出允许范围。");
            }
            else if (type == "checkbox" && value.Type != JTokenType.Boolean) Error("input.type", "必须为布尔值。");
            else if (type is "combobox" or "select" or "text" && value.Type != JTokenType.String)
            { Error("input.type", "必须为字符串选项。"); continue; }
            else if (type == "object")
            {
                if (value is not JObject nested) Error("input.type", "必须为对象。");
                else ValidateFields(field["fields"] as JArray ?? [], definition?["fields"] as JArray ?? [], nested, path + ".", templateId, issues);
            }
            else if (type is "table" or "removal_matrix")
            {
                if (value is not JArray rows) Error("input.type", "必须为数组。");
                else ValidateRows(field, definition, rows, path, issues);
            }
            if (definition?["options"] is JArray { Count: > 0 } options && !options.Any(o => JToken.DeepEquals(o, value)))
                Error("input.option", "选项无效。");
        }
    }

    static void ValidateRows(JToken field, JToken? definition, JArray rows, string path, List<ValidationIssue> issues)
    {
        var definitions = definition?["columns"] as JArray;
        var columns = field["columns"] as JArray ?? definitions;
        if (columns == null || definitions == null) return;
        for (int i = 0; i < rows.Count; i++)
        {
            if (rows[i] is not JObject row)
            { issues.Add(ValidationIssue.Error("input.row", ValidationStage.Input, $"{path}[{i}] 必须为对象。", $"{path}[{i}]")); continue; }
            ValidateFields(columns, definitions, row, $"{path}[{i}].", "", issues);
        }
    }

    static void ValidateMaterials(ProjectDocument document, PackageDefinition definition, MaterialCatalog catalog, List<ValidationIssue> issues)
    {
        var materials = catalog.Items.Values.Concat(definition.BaselineMaterials).GroupBy(m => m.Id).ToDictionary(g => g.Key, g => g.Last());
        foreach (var material in document.CustomMaterials)
        {
            materials[material.Id] = material;
            foreach (string error in FieldRules.MaterialErrors(material))
                issues.Add(ValidationIssue.Error("input.material", ValidationStage.Input, $"材料 {material.Name}：{error}", "CustomMaterials." + material.Id));
        }
        foreach (var duplicate in document.CustomMaterials.GroupBy(m => m.Id).Where(g => g.Count() > 1))
            issues.Add(ValidationIssue.Error("input.material.duplicate", ValidationStage.Input, $"重复自定义材料 {duplicate.Key}。", "CustomMaterials." + duplicate.Key));
        foreach (var selection in definition.MaterialSelections)
        {
            string group = selection["group_id"].Text(), path = "MaterialAssignments." + group;
            if (!document.MaterialAssignments.TryGetValue(group, out var id))
                issues.Add(ValidationIssue.Error("input.material.missing", ValidationStage.Input, $"缺少材料组 {group} 的选择。", path));
            else if (id.Length == 0 ? !((JArray)selection["options"]!).Any(o => o.Text() == "") :
                !materials.ContainsKey(id) || !((JArray)selection["options"]!).Any(o => o.Text() == "*" || o.Text() == id))
                issues.Add(ValidationIssue.Error("input.material.reference", ValidationStage.Input, $"材料 {id} 不适用于 {group}。", path));
        }
        foreach (string group in document.MaterialAssignments.Keys.Except(definition.MaterialSelections.Select(s => s["group_id"].Text())))
            issues.Add(ValidationIssue.Error("input.material.group", ValidationStage.Input, $"未知材料组 {group}。", "MaterialAssignments." + group));
    }

    static void ValidateRelations(ProjectDocument document, ValidationRules rules, List<ValidationIssue> issues)
    {
        var values = document.Values;
        bool Number(string key, out double number)
        {
            number = 0;
            return !issues.Any(i => i.ParameterPaths.Contains(key)) && values[key]?.Type is JTokenType.Integer or JTokenType.Float && double.IsFinite(number = values[key]!.Value<double>());
        }
        foreach (var rule in rules.Checks.Where(r => r["stage"].Text() == "input"))
        {
            void Add(string fallback, params string[] paths) => issues.Add(rules.Issue(rule, ValidationStage.Input, fallback, paths));
            switch (rule["check"].Text())
            {
                case "solder_ball_pitch":
                    if (Number("bga.diameter", out double diameter) && Number("bga.pitch", out double pitch) && diameter > pitch)
                        Add("焊球直径不能大于节距。", "bga.diameter", "bga.pitch");
                    break;
                case "via_dimensions":
                    if (!values["vias.enabled"].Flag()) break;
                    if (Number("vias.diameter", out double vd) && Number("vias.pitch", out double vp) && vd > vp)
                        Add("通孔直径不能大于节距。", "vias.diameter", "vias.pitch");
                    if (!(document.TemplateId == "chip_array" && values["vias.filled"].Flag()) &&
                        !issues.Any(i => i.ParameterPaths.Contains("vias.filled")) &&
                        Number("vias.plating", out double plating) && Number("vias.diameter", out vd) && (plating <= 0 || plating > vd / 2))
                        Add("通孔镀层厚度必须大于零且不超过孔半径。", "vias.plating", "vias.diameter");
                    break;
                case "sop_lead_count":
                    if (document.TemplateId == "sop" && Number("leads.total", out double count) && count % 2 != 0)
                        Add("SOP 引脚数量必须为偶数。", "leads.total");
                    break;
                case "metal_layers":
                    ValidateMetalLayers(values, rule, rules, issues);
                    break;
                case "array_layout":
                    if (!issues.Any(i => i.ParameterPaths.Contains("bga.representation")) && values["bga.representation"] is { Type: JTokenType.String } representation && representation.Value<string>() != "discrete" &&
                        (values["bga.ball_map_enabled"].Flag() || values["bga.omitted_cells"] is JArray { Count: > 0 }))
                        Add("显式去球及 Ball Map 需要离散建模。", "bga.representation", "bga.omitted_cells", "bga.ball_map");
                    break;
            }
        }
    }

    static void ValidateMetalLayers(JObject values, JToken rule, ValidationRules rules, List<ValidationIssue> issues)
    {
        if (values["metal.layers"] is not JArray rows) return;
        double height = values["substrate.thickness"]?.Type is JTokenType.Integer or JTokenType.Float ? values["substrate.thickness"]!.Value<double>() : double.NaN;
        for (int i = 0; i < rows.Count; i++)
        {
            string path = $"metal.layers[{i}]";
            if (rows[i] is not JObject row) continue;
            foreach (string key in new[] { "depth", "thickness", "coverage" })
            {
                string cell = path + "." + key;
                if (issues.Any(issue => issue.ParameterPaths.Contains(cell))) continue;
                if (row[key]?.Type is not (JTokenType.Integer or JTokenType.Float) || !double.IsFinite(row[key]!.Value<double>()))
                    issues.Add(ValidationIssue.Error("input.layer.number", ValidationStage.Input, $"{cell} 需要有限数值。", cell));
                else
                {
                    double n = row[key]!.Value<double>();
                    if (n < 0 || key == "thickness" && n == 0 || key == "coverage" && n > 100)
                        issues.Add(ValidationIssue.Error("input.layer.range", ValidationStage.Input, $"{cell} 超出允许范围。", cell));
                }
            }
            if (row["depth"]?.Type is JTokenType.Integer or JTokenType.Float && row["thickness"]?.Type is JTokenType.Integer or JTokenType.Float &&
                row["depth"]!.Value<double>() + row["thickness"]!.Value<double>() > height + 1e-10)
                issues.Add(rules.Issue(rule, ValidationStage.Input, "金属层必须位于基板内。", [path + ".depth", path + ".thickness", "substrate.thickness"]));
        }
    }
}
