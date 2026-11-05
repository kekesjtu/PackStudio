using Newtonsoft.Json.Linq;

namespace PackStudio.Core;

public static partial class InputValidator
{
    public static IReadOnlyList<ValidationIssue> Validate(ProjectDocument document, PackageDefinition definition, MaterialCatalog materials, ValidationRules rules)
    {
        var issues = new List<ValidationIssue>();
        void Error(string code, params string[] paths) => issues.Add(rules.Create(code, ValidationStage.Input, paths));
        if (string.IsNullOrWhiteSpace(document.Name) || document.Name.Length > 160)
            Error("input.name", "Name");
        if (document.TemplateId != definition.Info.Id) Error("input.template", "TemplateId");
        ValidateFields(rules.Fields, definition.Fields, document.Values, "", document.TemplateId, rules, issues);
        ValidateMaterials(document, definition, materials, rules, issues);
        ValidateRelations(document, rules, issues);
        issues.AddRange(ValidatePackageRelations(document, rules, issues));
        return issues.AsReadOnly();
    }

    static bool Active(JToken field, JObject values)
    {
        bool Numeric(string key) => values[key]?.Type is JTokenType.Integer or JTokenType.Float && double.IsFinite(values[key]!.Value<double>());
        if ((field["requires_numeric"] as JArray ?? []).Any(k => !Numeric(k.Text()))) return false;
        if ((field["requires_positive"] as JArray ?? []).Any(k => !Numeric(k.Text()) || values[k.Text()]!.Value<double>() <= 0)) return false;
        if (field["inactive_when"] is JObject inactive && JsonData.Matches(inactive, values)) return false;
        if (field["active_when"] is not JObject conditions) return true;
        if (conditions["all"] is JArray all) return all.All(c => JsonData.Matches(c as JObject, values));
        return JsonData.Matches(conditions, values);
    }

    static void ValidateFields(JArray fields, JArray definitions, JObject values, string prefix, string templateId, ValidationRules rules, List<ValidationIssue> issues)
    {
        foreach (var field in fields)
        {
            string key = field["key"].Text(), path = prefix + key;
            var definition = definitions.FirstOrDefault(f => f["key"].Text() == key);
            if (definition == null) throw new InvalidDataException($"校验规则引用未知参数 {path}。");
            if (definition["creation_only"].Flag() || !Active(field, values)) continue;
            string type = definition["type"].Text();
            var value = values[key];
            void Error(string code) => issues.Add(rules.Create(code, ValidationStage.Input, [path], field: field));
            if (value?.Type is null or JTokenType.Null)
            {
                if (field["required"]?.Value<bool>() != false && type is ("number" or "integer" or "integer_spinbox" or "checkbox" or "object" or "table" or "removal_matrix" or "combobox" or "select" or "text"))
                    Error("input.required");
                continue;
            }
            if (type is "number" or "integer" or "integer_spinbox")
            {
                if (value.Type is not (JTokenType.Float or JTokenType.Integer)) { Error("input.type.number"); continue; }
                double number = value.Value<double>();
                if (!double.IsFinite(number) || type.StartsWith("integer") && (number != Math.Truncate(number) || number < int.MinValue || number > int.MaxValue))
                { Error("input.number"); continue; }
                double minimum = field["minimum"]?.Type is JTokenType.Integer or JTokenType.Float ? field["minimum"]!.Value<double>() : double.NegativeInfinity;
                if (number < minimum || field["exclusive_minimum"]?.Type is JTokenType.Integer or JTokenType.Float && number <= field["exclusive_minimum"]!.Value<double>() || field["maximum"]?.Type is JTokenType.Integer or JTokenType.Float && number > field["maximum"]!.Value<double>())
                    Error("input.range");
            }
            else if (type == "checkbox" && value.Type != JTokenType.Boolean) Error("input.type.boolean");
            else if (type is "combobox" or "select" or "text" && value.Type != JTokenType.String)
            { Error("input.type.string"); continue; }
            else if (type == "object")
            {
                if (value is not JObject nested) Error("input.type.object");
                else ValidateFields(field["fields"] as JArray ?? [], definition?["keys"] as JArray ?? [], nested, path + ".", templateId, rules, issues);
            }
            else if (type is "table" or "removal_matrix")
            {
                if (value is not JArray rows) Error("input.type.array");
                else ValidateRows(field, definition, rows, path, rules, issues);
            }
            if (definition != null && PackageDefinition.OptionValues(definition) is { Count: > 0 } options && !options.Any(o => JToken.DeepEquals(o, value)))
                Error("input.option");
        }
    }

    static void ValidateRows(JToken field, JToken? definition, JArray rows, string path, ValidationRules rules, List<ValidationIssue> issues)
    {
        var definitions = definition?["columns"] as JArray;
        var columns = field["columns"] as JArray ?? definitions;
        if (columns == null || definitions == null) return;
        if (field["min_rows"] is JToken min && rows.Count < min.Value<int>() || field["max_rows"] is JToken max && rows.Count > max.Value<int>())
            issues.Add(rules.Create("input.rows", ValidationStage.Input, [path], field: field));
        for (int i = 0; i < rows.Count; i++)
        {
            if (rows[i] is not JObject row)
            { issues.Add(rules.Create("input.row", ValidationStage.Input, [$"{path}[{i}]"])); continue; }
            if (row.Properties().Any(p => !definitions.Any(c => c["key"].Text() == p.Name)))
                issues.Add(rules.Create("input.row.columns", ValidationStage.Input, [$"{path}[{i}]"], field: field));
            ValidateFields(columns, definitions, row, $"{path}[{i}].", "", rules, issues);
        }
    }

    internal static void ValidateMaterials(ProjectDocument document, PackageDefinition definition, MaterialCatalog catalog, ValidationRules rules, List<ValidationIssue> issues)
    {
        var materials = catalog.Items.ToDictionary(p => p.Key, p => p.Value);
        foreach (var material in document.CustomMaterials)
        {
            materials[material.Id] = material;
            foreach (string error in FieldRules.MaterialErrors(material, rules))
                issues.Add(rules.Create("input.material", ValidationStage.Input, ["CustomMaterials." + material.Id], detail: material.Name, reason: error));
        }
        foreach (var duplicate in document.CustomMaterials.GroupBy(m => m.Id).Where(g => g.Count() > 1))
            issues.Add(rules.Create("input.material.duplicate", ValidationStage.Input, ["CustomMaterials." + duplicate.Key], detail: duplicate.Key));
        foreach (var selection in definition.MaterialSelections)
        {
            string group = selection["key"].Text(), path = "MaterialAssignments." + group;
            if (!document.MaterialAssignments.TryGetValue(group, out var id))
                issues.Add(rules.Create("input.material.missing", ValidationStage.Input, [path], detail: group));
            else if (id.Length == 0 ? !(PackageDefinition.OptionValues(selection)).Any(o => o.Text() == "") :
                !materials.ContainsKey(id) || !(PackageDefinition.OptionValues(selection)).Any(o => o.Text() == "*" || o.Text() == id))
                issues.Add(rules.Create("input.material.reference", ValidationStage.Input, [path], detail: id));
        }
        foreach (string group in document.MaterialAssignments.Keys.Except(definition.MaterialSelections.Select(s => s["key"].Text())))
            issues.Add(rules.Create("input.material.group", ValidationStage.Input, ["MaterialAssignments." + group], detail: group));
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
            void Add(params string[] paths) => issues.Add(rules.Create(rule["id"].Text(), ValidationStage.Input, paths));
            switch (rule["check"].Text())
            {
                case "solder_ball_pitch":
                    if (Number("bga.diameter", out double diameter) && Number("bga.pitch", out double pitch) && diameter > pitch)
                        Add("bga.diameter", "bga.pitch");
                    break;
                case "via_pitch":
                    if (!values["vias.enabled"].Flag()) break;
                    if (Number("vias.diameter", out double vd) && Number("vias.pitch", out double vp) && vd > vp)
                        Add("vias.diameter", "vias.pitch");
                    break;
                case "via_plating":
                    if (!values["vias.enabled"].Flag()) break;
                    if (!(document.TemplateId == "chip_array" && values["vias.filled"].Flag()) &&
                        !issues.Any(i => i.ParameterPaths.Contains("vias.filled")) &&
                        Number("vias.plating", out double plating) && Number("vias.diameter", out double viaDiameter) && (plating <= 0 || plating > viaDiameter / 2))
                        Add("vias.plating", "vias.diameter");
                    break;
                case "sop_lead_count":
                    if (document.TemplateId == "sop" && Number("leads.total", out double count) && count % 2 != 0)
                        Add("leads.total");
                    break;
                case "metal_layers":
                    ValidateMetalLayers(values, rule, rules, issues);
                    break;
                case "array_layout":
                    if (!issues.Any(i => i.ParameterPaths.Contains("bga.representation")) && values["bga.representation"] is { Type: JTokenType.String } representation && representation.Value<string>() != "discrete" &&
                        (values["bga.ball_map_enabled"].Flag() || values["bga.omitted_cells"] is JArray { Count: > 0 }))
                        Add("bga.representation", "bga.omitted_cells", "bga.ball_map");
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
            if (row["depth"]?.Type is JTokenType.Integer or JTokenType.Float && row["thickness"]?.Type is JTokenType.Integer or JTokenType.Float &&
                row["depth"]!.Value<double>() + row["thickness"]!.Value<double>() > height + 1e-10)
                issues.Add(rules.Create(rule["id"].Text(), ValidationStage.Input, [path + ".depth", path + ".thickness", "substrate.thickness"]));
        }
    }
}
